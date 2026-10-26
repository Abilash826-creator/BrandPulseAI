import uuid
import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings

class CrisisDetector:
    def __init__(self):
        self.negative_threshold = settings.CRISIS_NEGATIVE_THRESHOLD
        self.volume_multiplier = settings.CRISIS_VOLUME_MULTIPLIER

    def calculate_crisis_risk(self, recent_mentions: List[Dict[str, Any]], baseline_mentions: Optional[List[Dict[str, Any]]] = None) -> Tuple[float, str, Optional[Dict[str, Any]]]:
        """
        Evaluates real-time mentions to determine crisis risk score (0-100),
        severity level (none, low, medium, critical), and trigger alert payload if threshold exceeded.
        """
        if not recent_mentions:
            return 0.0, "none", None

        total = len(recent_mentions)
        negatives = [m for m in recent_mentions if m.get("sentiment") == "negative"]
        neg_count = len(negatives)
        neg_ratio = neg_count / total if total > 0 else 0.0

        # Anger & Fear ratio
        anger_mentions = [m for m in recent_mentions if m.get("dominant_emotion") in ["anger", "fear"]]
        anger_ratio = len(anger_mentions) / total if total > 0 else 0.0

        # Viral negative posts
        viral_negatives = [m for m in negatives if m.get("virality_score", 0) > 70 or m.get("reach", 0) > 15000]

        # Calculate composite Crisis Risk Index (0.0 to 100.0)
        risk_score = (neg_ratio * 45.0) + (anger_ratio * 25.0) + (min(len(viral_negatives) * 15.0, 30.0))
        risk_score = round(min(max(risk_score, 0.0), 100.0), 1)

        # Baseline volume anomaly
        volume_anomaly = False
        if baseline_mentions and len(baseline_mentions) > 0:
            avg_hourly_baseline = len(baseline_mentions) / 24.0
            if total > avg_hourly_baseline * self.volume_multiplier and neg_ratio > 0.3:
                volume_anomaly = True
                risk_score = min(risk_score + 15.0, 100.0)

        # Determine Severity Level
        severity = "none"
        if risk_score >= 75.0 or len(viral_negatives) >= 3:
            severity = "critical"
        elif risk_score >= 45.0 or len(viral_negatives) >= 1:
            severity = "medium"
        elif risk_score >= 25.0:
            severity = "low"

        # Construct alert details if severity is not none
        alert_payload = None
        if severity in ["low", "medium", "critical"]:
            top_complaint = negatives[0].get("content", "Spike in negative sentiment") if negatives else "Customer dissatisfaction detected"
            
            # Root cause detection
            causes = []
            if len(viral_negatives) > 0:
                causes.append(f"High-virality negative post by @{viral_negatives[0].get('author_handle', 'user')} on {viral_negatives[0].get('platform', 'social media')}")
            if anger_ratio > 0.3:
                causes.append(f"Aggravated customer emotion (Anger/Fear index at {round(anger_ratio*100, 1)}%)")
            if neg_ratio > 0.4:
                causes.append(f"Abnormal negative sentiment ratio ({round(neg_ratio*100, 1)}% vs baseline 12%)")
            if volume_anomaly:
                causes.append("Sudden volume spike exceeding 2.0x standard hourly traffic")

            root_cause_summary = " & ".join(causes) if causes else "Elevated negative consumer chatter and friction."

            recommendations = self._generate_recommendations(severity, viral_negatives, anger_ratio)

            alert_payload = {
                "id": f"alert_{uuid.uuid4().hex[:8]}",
                "title": f"[{severity.upper()}] Crisis Risk Spike Detected ({risk_score}%)",
                "severity": severity,
                "metric_type": "negative_sentiment_spike" if neg_ratio > 0.35 else "viral_negative_post",
                "trigger_value": risk_score,
                "threshold_value": 45.0,
                "description": f"Real-time sentiment anomaly: {neg_count}/{total} negative mentions with peak anger indices.",
                "ai_root_cause": root_cause_summary,
                "recommendations": recommendations,
                "status": "active",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

        return risk_score, severity, alert_payload

    def _generate_recommendations(self, severity: str, viral_negatives: List[Dict[str, Any]], anger_ratio: float) -> List[str]:
        recs = []
        if severity == "critical":
            recs.append("Trigger Level-1 PR Crisis Escalation to VP of Communications and Product Lead.")
            recs.append("Publish official transparency note or incident status page update immediately.")
            recs.append("Directly respond to top viral influencer threads offering direct executive support escalation.")
            recs.append("Temporarily pause automated outbound promotional ad campaigns.")
        elif severity == "medium":
            recs.append("Brief Customer Support tier 2 team with pre-approved FAQ responses.")
            recs.append("Monitor sentiment trajectory every 15 minutes for escalation indicators.")
            recs.append("Prioritize public replies to verified query and complaint tweets.")
        else:
            recs.append("Log issue in triage queue and track keyword frequency over the next 4 hours.")
            recs.append("Engage with dissatisfied users with helpful documentation links.")
        return recs

crisis_detector = CrisisDetector()
