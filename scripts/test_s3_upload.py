import boto3
from dotenv import load_dotenv
import os

import sys

# 1. Load Env
if len(sys.argv) < 2:
    print("Usage: python3 test_s3_upload.py <path_to_env_file>")
    sys.exit(1)

env_file = sys.argv[1]
print(f"Loading environment from: {env_file}")
load_dotenv(env_file, override=True)

# 2. Config
region = os.getenv("AWS_REGION", "ap-south-1")
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
bucket_name = os.getenv("S3_BUCKET_NAME")

print(f"Loaded Config -> Region: {region}, Bucket: {bucket_name}")

# 3. Init Client
s3 = boto3.client(
    's3',
    region_name=region,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
)

def test_upload_and_sign():
    filename = "test_upload_s3.txt"
    content = b"This is a verified upload from the S3 Test Script."
    
    # Upload
    print(f"\nUploading {filename}...")
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=content,
            ContentType="text/plain"
        )
        print("✅ PutObject Successful.")
        
        # Verify Read Access (GetObject)
        print(f"\nVerifying Read Access (GetObject)...")
        try:
            s3.get_object(Bucket=bucket_name, Key=filename)
            print("✅ GetObject Successful (Read access confirmed).")
        except Exception as e:
             print(f"❌ GetObject Failed! This user likely lacks 's3:GetObject' permission.")
             print(f"   Error: {e}")

        # Presigned URL (Guaranteed to Work only if user has GetObject permission)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': filename},
            ExpiresIn=3600 # 1 Hour
        )
        print(f"\n🔑 SECURE PRESIGNED URL (Click this to see content):")
        print(f"{presigned_url}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_upload_and_sign()
