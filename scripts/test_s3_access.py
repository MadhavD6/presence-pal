import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

def test_s3_access(env_file):
    print(f"Testing environment: {env_file}")
    
    # clear existing env vars that might interfere (optional, but good for cleanliness if running back to back)
    # actually load_dotenv with override=True is better
    load_dotenv(env_file, override=True)
    
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION")
    bucket_name = os.getenv("S3_BUCKET_NAME")

    print(f"Configuration loaded:")
    print(f"  Access Key: {'*' * 16 + aws_access_key[-4:] if aws_access_key else 'None'} (Len: {len(aws_access_key) if aws_access_key else 0})")
    print(f"  Secret Key: {'*' * (len(aws_secret_key)-4) + aws_secret_key[-4:] if aws_secret_key else 'None'} (Len: {len(aws_secret_key) if aws_secret_key else 0})")
    print(f"  Region: {region}")
    
    if not all([aws_access_key, aws_secret_key, region, bucket_name]):
        print("❌ Error: Missing required environment variables.")
        return False

    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        
        # 1. Check if we can list buckets (verifies generic access/credentials)
        try:
            print("Attempting to list buckets check credentials...")
            s3.list_buckets()
            print("✅ Credentials are valid (list_buckets succeeded).")
        except ClientError as e:
            print(f"⚠️  Could not list buckets (Error: {e.response['Error']['Code']}). Credentials might be limited scope or invalid.")

        print(f"Attempting to connect to bucket '{bucket_name}'...")
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ Success! Credentials function and have access to bucket '{bucket_name}'.")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ Connection Failed. Error Code: {error_code}")
        print(f"Message: {e}")
        if error_code == '403':
            print("Tip: Check Access Key, Secret Key, and if this user has permission for this bucket.")
        elif error_code == '404':
            print("Tip: Bucket does not exist or region is incorrect.")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_s3_access.py <path_to_env_file>")
        sys.exit(1)
        
    env_file_path = sys.argv[1]
    if not os.path.exists(env_file_path):
        print(f"File not found: {env_file_path}")
        sys.exit(1)
        
    success = test_s3_access(env_file_path)
    if not success:
        sys.exit(1)
