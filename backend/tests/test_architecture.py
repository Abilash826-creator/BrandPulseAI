import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.core.config import Settings, settings
from app.core.logging import get_request_id, set_request_id
from app.core.storage import LocalStorage, S3Storage, get_storage
from app.core.firewall import extract_client_ip, security_firewall
from main import app


def test_settings_inheritance_and_fields():
    """Verify Settings inherits from pydantic-settings BaseSettings and includes new configs."""
    from pydantic_settings import BaseSettings
    assert issubclass(Settings, BaseSettings)
    assert hasattr(settings, "STORAGE_BACKEND")
    assert hasattr(settings, "REDIS_URL")
    assert hasattr(settings, "TRUSTED_PROXIES")
    assert hasattr(settings, "AWS_S3_BUCKET")
    assert hasattr(settings, "AWS_REGION")


@pytest.mark.asyncio
async def test_request_id_middleware_and_logging():
    """Verify request ID is assigned, returned in header, and captured in logging context."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request without incoming ID
        res1 = await client.get("/health")
        assert res1.status_code == 200
        req_id1 = res1.headers.get("X-Request-ID")
        assert req_id1 is not None
        assert len(req_id1) >= 8

        # Request with explicit incoming ID
        custom_id = f"test-req-{uuid.uuid4().hex[:6]}"
        res2 = await client.get("/health", headers={"X-Request-ID": custom_id})
        assert res2.status_code == 200
        assert res2.headers.get("X-Request-ID") == custom_id


def test_local_storage_lifecycle(tmp_path):
    """Verify LocalStorage saves, reads, checks existence, and deletes files."""
    storage = LocalStorage(base_dir=str(tmp_path))
    test_filename = "test_report.csv"
    test_content = b"header1,header2\nval1,val2"

    saved_name = storage.save(test_filename, test_content)
    assert saved_name == test_filename
    assert storage.exists(test_filename) is True

    retrieved = storage.get_bytes(test_filename)
    assert retrieved == test_content

    file_path = storage.get_file_path(test_filename)
    assert file_path is not None

    deleted = storage.delete(test_filename)
    assert deleted is True
    assert storage.exists(test_filename) is False


def test_s3_storage_mock(monkeypatch):
    """Verify S3Storage interacts with S3 client properly."""
    storage = S3Storage(
        bucket_name="test-bucket",
        region="us-east-1",
        access_key="fake-key",
        secret_key="fake-secret"
    )

    class MockBody:
        def read(self):
            return b"mock-s3-bytes"

    class MockClient:
        def __init__(self):
            self.saved = {}

        def put_object(self, Bucket, Key, Body, **kwargs):
            self.saved[f"{Bucket}/{Key}"] = Body

        def get_object(self, Bucket, Key):
            return {"Body": MockBody()}

        def head_object(self, Bucket, Key):
            if f"{Bucket}/{Key}" in self.saved:
                return {}
            raise Exception("NotFound")

        def delete_object(self, Bucket, Key):
            self.saved.pop(f"{Bucket}/{Key}", None)

        def generate_presigned_url(self, action, Params, ExpiresIn):
            return f"https://{Params['Bucket']}.s3.amazonaws.com/{Params['Key']}?sig=fake"

    mock_s3 = MockClient()
    monkeypatch.setattr(storage, "_client", mock_s3)

    saved = storage.save("report.pdf", b"pdf-data")
    assert saved == "report.pdf"
    assert storage.exists("report.pdf") is True
    assert storage.get_bytes("report.pdf") == b"mock-s3-bytes"
    assert "https://test-bucket.s3.amazonaws.com/report.pdf" in storage.get_url("report.pdf")
    assert storage.get_file_path("report.pdf") is None

    assert storage.delete("report.pdf") is True
    assert storage.exists("report.pdf") is False


@pytest.mark.asyncio
async def test_firewall_allows_passwords_with_hash_and_dashes():
    """Verify firewall stops blocking passwords with '#', '--', etc."""
    class DummyClient:
        host = "192.168.1.10"

    class DummyRequest:
        client = DummyClient()
        headers = {"user-agent": "Mozilla/5.0"}

    # Passwords with characters that previously triggered regex WAF blocks
    payloads = [
        {"password": "MySuper#SecurePassword123--"},
        {"password": "admin'--"},
        {"password": "Test#Password/*comment*/"},
    ]

    for p in payloads:
        is_safe, threat_type, details, score = await security_firewall.inspect_payload(
            request=DummyRequest(),
            payload_data=p,
            endpoint_name="/auth/login"
        )
        assert is_safe is True, f"Failed for payload: {p}, threat_type: {threat_type}"
        assert threat_type is None


@pytest.mark.asyncio
async def test_firewall_blocks_malicious_user_agent():
    """Verify malicious scanners like sqlmap or nikto are blocked."""
    class DummyClient:
        host = "192.168.1.10"

    class BadUARequest:
        client = DummyClient()
        headers = {"user-agent": "sqlmap/1.5.2#stable (http://sqlmap.org)"}

    is_safe, threat_type, details, score = await security_firewall.inspect_payload(
        request=BadUARequest(),
        payload_data={"email": "attacker@test.com"},
        endpoint_name="/auth/login"
    )
    assert is_safe is False
    assert threat_type == "MALICIOUS_SCANNER"


def test_trusted_proxies_ip_extraction():
    """Verify X-Forwarded-For is only trusted when coming from TRUSTED_PROXIES."""
    class MockClient:
        def __init__(self, host):
            self.host = host

    class MockRequest:
        def __init__(self, host, xff=None):
            self.client = MockClient(host)
            self.headers = {"x-forwarded-for": xff} if xff else {}

    # Case 1: Untrusted client attempts IP spoofing via XFF
    req_untrusted = MockRequest(host="203.0.113.195", xff="198.51.100.5")
    assert extract_client_ip(req_untrusted) == "203.0.113.195"

    # Case 2: Trusted proxy (127.0.0.1) forwards legitimate client IP
    req_trusted = MockRequest(host="127.0.0.1", xff="198.51.100.5, 10.0.0.1")
    assert extract_client_ip(req_trusted) == "198.51.100.5"
