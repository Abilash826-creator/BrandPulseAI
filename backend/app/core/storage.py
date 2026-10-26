import os
import io
import logging
from abc import ABC, abstractmethod
from typing import Optional, Union
from app.core.config import settings

logger = logging.getLogger("brandpulse.storage")


class BaseStorage(ABC):
    """
    Abstract Storage Interface for persistent reports and assets.
    """
    @abstractmethod
    def save(self, filename: str, data: Union[bytes, str], content_type: Optional[str] = None) -> str:
        """Saves file content and returns identifier/filename."""
        pass

    @abstractmethod
    def get_bytes(self, filename: str) -> bytes:
        """Retrieves raw file bytes."""
        pass

    @abstractmethod
    def get_file_path(self, filename: str) -> Optional[str]:
        """Returns local absolute path if file exists locally, otherwise None."""
        pass

    @abstractmethod
    def get_url(self, filename: str) -> str:
        """Returns download URL or pre-signed URL for the stored file."""
        pass

    @abstractmethod
    def exists(self, filename: str) -> bool:
        """Checks if file exists in storage."""
        pass

    @abstractmethod
    def delete(self, filename: str) -> bool:
        """Deletes file from storage."""
        pass


class LocalStorage(BaseStorage):
    """
    Local filesystem storage implementation.
    """
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or settings.REPORTS_DIR
        os.makedirs(self.base_dir, exist_ok=True)

    def save(self, filename: str, data: Union[bytes, str], content_type: Optional[str] = None) -> str:
        safe_name = os.path.basename(filename)
        dest_path = os.path.join(self.base_dir, safe_name)
        mode = "wb" if isinstance(data, (bytes, bytearray)) else "w"
        encoding = None if isinstance(data, (bytes, bytearray)) else "utf-8"
        
        with open(dest_path, mode, encoding=encoding) as f:
            f.write(data)
        logger.info(f"[LocalStorage] Saved file: {safe_name} to {dest_path}")
        return safe_name

    def get_bytes(self, filename: str) -> bytes:
        safe_name = os.path.basename(filename)
        file_path = os.path.join(self.base_dir, safe_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{safe_name}' not found in local storage.")
        with open(file_path, "rb") as f:
            return f.read()

    def get_file_path(self, filename: str) -> Optional[str]:
        safe_name = os.path.basename(filename)
        file_path = os.path.join(self.base_dir, safe_name)
        if os.path.exists(file_path):
            return file_path
        return None

    def get_url(self, filename: str) -> str:
        safe_name = os.path.basename(filename)
        return f"/api/v1/reports/download/{safe_name}"

    def exists(self, filename: str) -> bool:
        safe_name = os.path.basename(filename)
        return os.path.exists(os.path.join(self.base_dir, safe_name))

    def delete(self, filename: str) -> bool:
        safe_name = os.path.basename(filename)
        file_path = os.path.join(self.base_dir, safe_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError as e:
                logger.warning(f"[LocalStorage] Could not delete {safe_name}: {e}")
                return False
        return False


class S3Storage(BaseStorage):
    """
    S3-compatible storage implementation (AWS S3, MinIO, Cloudflare R2, LocalStack).
    """
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        self.bucket = bucket_name or settings.AWS_S3_BUCKET
        self.region = region or settings.AWS_REGION
        self.endpoint_url = endpoint_url or settings.AWS_ENDPOINT_URL or None
        self.access_key = access_key or settings.AWS_ACCESS_KEY_ID or None
        self.secret_key = secret_key or settings.AWS_SECRET_ACCESS_KEY or None
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import boto3
                kwargs = {
                    "region_name": self.region,
                }
                if self.endpoint_url:
                    kwargs["endpoint_url"] = self.endpoint_url
                if self.access_key and self.secret_key:
                    kwargs["aws_access_key_id"] = self.access_key
                    kwargs["aws_secret_access_key"] = self.secret_key
                self._client = boto3.client("s3", **kwargs)
            except Exception as e:
                logger.error(f"[S3Storage] Failed to initialize boto3 client: {e}")
                raise
        return self._client

    def save(self, filename: str, data: Union[bytes, str], content_type: Optional[str] = None) -> str:
        safe_name = os.path.basename(filename)
        body = data.encode("utf-8") if isinstance(data, str) else data
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.put_object(
            Bucket=self.bucket,
            Key=safe_name,
            Body=body,
            **extra_args
        )
        logger.info(f"[S3Storage] Uploaded {safe_name} to s3://{self.bucket}/{safe_name}")
        return safe_name

    def get_bytes(self, filename: str) -> bytes:
        safe_name = os.path.basename(filename)
        response = self.client.get_object(Bucket=self.bucket, Key=safe_name)
        return response["Body"].read()

    def get_file_path(self, filename: str) -> Optional[str]:
        # S3 storage is remote, no local path by default
        return None

    def get_url(self, filename: str) -> str:
        safe_name = os.path.basename(filename)
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": safe_name},
                ExpiresIn=3600
            )
            return url
        except Exception as e:
            logger.warning(f"[S3Storage] Could not generate presigned URL: {e}")
            return f"/api/v1/reports/download/{safe_name}"

    def exists(self, filename: str) -> bool:
        safe_name = os.path.basename(filename)
        try:
            self.client.head_object(Bucket=self.bucket, Key=safe_name)
            return True
        except Exception:
            return False

    def delete(self, filename: str) -> bool:
        safe_name = os.path.basename(filename)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=safe_name)
            return True
        except Exception as e:
            logger.warning(f"[S3Storage] Could not delete s3://{self.bucket}/{safe_name}: {e}")
            return False


def get_storage() -> BaseStorage:
    """
    Returns the configured storage backend based on STORAGE_BACKEND setting.
    """
    backend_type = settings.STORAGE_BACKEND.lower().strip()
    if backend_type == "s3" and settings.AWS_S3_BUCKET:
        return S3Storage()
    return LocalStorage()


storage = get_storage()
