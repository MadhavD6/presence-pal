import boto3
from botocore.exceptions import NoCredentialsError
from backend.core.config import get_settings
from backend.core.logger import logger
import os

settings = get_settings()

class StorageService:
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

    def upload_file(self, file_bytes: bytes, object_name: str, content_type: str = "image/jpeg") -> str:
        """
        Upload a file to S3 and return the public URL (or key).
        """
        try:
            # Check if credentials are valid in settings before attempting
            if not settings.AWS_ACCESS_KEY_ID or settings.AWS_ACCESS_KEY_ID == "dummy":
                if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_ACCESS_KEY_ID") != "dummy":
                     # Fallback to system env if settings are stale but env is present (unlikely with pydantic, but safe)
                     pass
                else:
                    logger.warning("S3 Credentials missing. skipping upload.")
                    return None

            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_bytes,
                ContentType=content_type,
                # ACL='public-read' # Optional: Make it public if needed, or use presigned URLs
            )
            # Construct URL (Standard S3 URL format)
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_name}"
            return url
        except Exception as e:
            logger.error(f"S3 Upload Error: {e}")
            # Fallback: Return None or a local path reference if critical
            return None

storage_service = StorageService()
