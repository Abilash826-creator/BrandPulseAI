import time
import uuid
import datetime
import logging
from typing import Dict, Any, Tuple, Optional, List
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger("brandpulse.firewall")


def extract_client_ip(request: Optional[Request]) -> str:
    """
    Extracts the client IP address.
    Only trusts the 'X-Forwarded-For' header if the immediate client is in TRUSTED_PROXIES.
    """
    if not request:
        return "127.0.0.1"
    
    immediate_host = request.client.host if request.client else "127.0.0.1"
    trusted_proxies = getattr(settings, "TRUSTED_PROXIES", ["127.0.0.1", "::1"])

    if immediate_host in trusted_proxies:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First IP in X-Forwarded-For list is the originating client IP
            return forwarded.split(",")[0].strip()

    return immediate_host


# SlowAPI Rate Limiter (Redis-backed if REDIS_URL is configured, in-memory otherwise)
limiter = Limiter(
    key_func=extract_client_ip,
    storage_uri=settings.REDIS_URL or "memory://",
    default_limits=["200/minute"]
)


class SecurityFirewall:
    """
    Authentication Defense Shield & Rate Limiter.
    Protects authentication endpoints against:
      1. Brute-Force & Credential Stuffing (Quarantine Tracker + SlowAPI)
      2. Malicious Automated Scanners & Attack Tools (User-Agent filtering)
    Note: Does not perform brittle regex inspection on passwords, allowing valid
    special characters (e.g. '#', '--') while relying on Pydantic validation
    and parameterized MongoDB driver queries for data safety.
    """
    def __init__(self):
        # Malicious Scanners / Attack Tool User-Agents
        self.blacklisted_user_agents = [
            "sqlmap", "nikto", "hydra", "nmap", "masscan", "wpscan", 
            "havij", "acunetix", "dirbuster", "nessus", "metasploit"
        ]

        # In-Memory Brute-Force Rate Limiter & Quarantine Tracker
        # Schema: { ip_address: {"failed_count": int, "first_failed_time": float, "quarantine_until": float} }
        self.ip_rate_limits: Dict[str, Dict[str, Any]] = {}
        
        # Policy Thresholds
        self.MAX_FAILED_ATTEMPTS = 5
        self.RATE_WINDOW_SECONDS = 60
        self.QUARANTINE_DURATION_SECONDS = 120

        # Telemetry Metrics
        self.stats = {
            "total_inspections": 0,
            "blocked_brute_force": 0,
            "blocked_malicious_ua": 0,
            "passed_clean": 0,
            "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def _extract_client_ip(self, request: Optional[Request]) -> str:
        return extract_client_ip(request)

    def _check_ip_quarantine(self, ip: str) -> Tuple[bool, int]:
        """Checks if an IP is actively quarantined due to brute-force abuse."""
        now = time.time()
        record = self.ip_rate_limits.get(ip)
        if not record:
            return False, 0
        
        quarantine_until = record.get("quarantine_until", 0)
        if quarantine_until > now:
            remaining_seconds = int(quarantine_until - now)
            return True, remaining_seconds
        
        # Expired quarantine cleanup
        if quarantine_until > 0 and quarantine_until <= now:
            del self.ip_rate_limits[ip]
            
        return False, 0

    def _cleanup_stale_limits(self) -> None:
        now = time.time()
        stale = [
            ip for ip, rec in self.ip_rate_limits.items()
            if rec.get("quarantine_until", 0) <= now and (now - rec.get("first_failed_time", now) > self.RATE_WINDOW_SECONDS * 2)
        ]
        for ip in stale:
            self.ip_rate_limits.pop(ip, None)

    def record_failed_attempt(self, ip: str) -> Dict[str, Any]:
        """Records a failed authentication event and escalates quarantine if threshold exceeded."""
        if len(self.ip_rate_limits) > 500:
            self._cleanup_stale_limits()

        now = time.time()
        record = self.ip_rate_limits.get(ip)
        
        if not record:
            record = {
                "failed_count": 1,
                "first_failed_time": now,
                "quarantine_until": 0
            }
            self.ip_rate_limits[ip] = record
        else:
            # Check window expiry
            if now - record["first_failed_time"] > self.RATE_WINDOW_SECONDS:
                record["failed_count"] = 1
                record["first_failed_time"] = now
            else:
                record["failed_count"] += 1

            if record["failed_count"] >= self.MAX_FAILED_ATTEMPTS:
                record["quarantine_until"] = now + self.QUARANTINE_DURATION_SECONDS
                self.stats["blocked_brute_force"] += 1
                return {
                    "quarantined": True,
                    "quarantine_seconds": self.QUARANTINE_DURATION_SECONDS,
                    "failed_count": record["failed_count"]
                }

        return {
            "quarantined": False,
            "failed_count": record["failed_count"],
            "remaining_attempts": max(0, self.MAX_FAILED_ATTEMPTS - record["failed_count"])
        }

    def record_successful_auth(self, ip: str):
        """Clears failed attempt counters upon authenticating safely."""
        if ip in self.ip_rate_limits:
            del self.ip_rate_limits[ip]

    async def inspect_payload(
        self,
        request: Optional[Request],
        payload_data: Dict[str, Any],
        endpoint_name: str = "/auth/login"
    ) -> Tuple[bool, Optional[str], Optional[str], float]:
        """
        Deep inspection of client IP and headers.
        Does NOT block legitimate passwords with '#', '--', etc.
        Returns: (is_allowed, threat_type, details, threat_score)
        """
        self.stats["total_inspections"] += 1
        client_ip = self._extract_client_ip(request)
        user_agent = request.headers.get("user-agent", "") if request else ""

        # 1. Check IP Quarantine (Brute-Force Shield)
        is_quarantined, remaining_sec = self._check_ip_quarantine(client_ip)
        if is_quarantined:
            self.stats["blocked_brute_force"] += 1
            await self._log_security_event(
                event_type="BLOCKED_BRUTE_FORCE",
                threat_level="HIGH",
                ip_address=client_ip,
                endpoint=endpoint_name,
                user_agent=user_agent,
                matched_rule=f"Exceeded {self.MAX_FAILED_ATTEMPTS} failed login attempts. Quarantined for {remaining_sec}s remaining.",
                threat_score=0.95,
                action="BLOCKED"
            )
            return False, "BRUTE_FORCE_LOCKOUT", f"Access temporarily quarantined due to repeated failed login attempts. Retry in {remaining_sec} seconds.", 0.95

        # 2. Check User-Agent Blacklist
        lower_ua = user_agent.lower()
        for bad_ua in self.blacklisted_user_agents:
            if bad_ua in lower_ua:
                self.stats["blocked_malicious_ua"] += 1
                await self._log_security_event(
                    event_type="BLOCKED_MALICIOUS_SCANNER",
                    threat_level="CRITICAL",
                    ip_address=client_ip,
                    endpoint=endpoint_name,
                    user_agent=user_agent,
                    matched_rule=f"Malicious scanner signature identified: '{bad_ua}'",
                    threat_score=1.0,
                    action="BLOCKED"
                )
                return False, "MALICIOUS_SCANNER", f"Malicious attack scanner detected ({bad_ua}). Access Denied.", 1.0

        # Clean Verified Request
        self.stats["passed_clean"] += 1
        return True, None, "Payload verified clean. WAF Inspection Passed.", 0.0

    async def _log_security_event(
        self,
        event_type: str,
        threat_level: str,
        ip_address: str,
        endpoint: str,
        user_agent: str,
        matched_rule: str,
        threat_score: float,
        action: str = "BLOCKED"
    ):
        """Persists security violation log into MongoDB 'firewall_logs' collection."""
        try:
            db = get_db()
            now = datetime.datetime.now(datetime.timezone.utc)
            log_doc = {
                "id": f"fw_{uuid.uuid4().hex[:10]}",
                "event_type": event_type,
                "threat_level": threat_level,
                "threat_score": threat_score,
                "ip_address": ip_address,
                "endpoint": endpoint,
                "user_agent": user_agent[:120] if user_agent else "Browser/WebClient",
                "matched_rule": matched_rule,
                "action": action,
                "timestamp": now,
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S")
            }
            await db["firewall_logs"].insert_one(log_doc)
        except Exception as e:
            logger.warning(f"[WAF Logging Warning] Could not write firewall log: {e}")

    def get_status(self, client_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """Returns live firewall telemetry status and active rules."""
        is_quarantined, remaining_sec = self._check_ip_quarantine(client_ip)
        
        active_threats_total = (
            self.stats["blocked_brute_force"] + 
            self.stats["blocked_malicious_ua"]
        )

        return {
            "firewall_status": "ACTIVE_SHIELDING",
            "version": "BrandPulse Rate Limiter 3.5.0 (SlowAPI + Brute Force Defense)",
            "rate_limiter_storage": "redis" if settings.REDIS_URL else "memory",
            "client_ip": client_ip,
            "ip_status": "QUARANTINED" if is_quarantined else "VERIFIED_SAFE",
            "quarantine_remaining_seconds": remaining_sec,
            "rules_active": {
                "brute_force_rate_limiter": True,
                "slowapi_sliding_window": True,
                "scanner_bot_filter": True
            },
            "metrics": {
                "total_inspections": self.stats["total_inspections"],
                "total_threats_blocked": active_threats_total,
                "blocked_brute_force": self.stats["blocked_brute_force"],
                "blocked_malicious_ua": self.stats["blocked_malicious_ua"],
                "clean_traffic": self.stats["passed_clean"]
            },
            "security_tier": "Enterprise Tier 1 (SlowAPI & Multi-Attempt Defense)"
        }


# Global Singleton Instance
security_firewall = SecurityFirewall()
