import boto3
from botocore.client import Config

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

bucket = "raw"

# Borrar objetos dentro del bucket
objects = s3.list_objects_v2(Bucket=bucket)
if "Contents" in objects:
    for obj in objects["Contents"]:
        s3.delete_object(Bucket=bucket, Key=obj["Key"])

# Borrar bucket
s3.delete_bucket(Bucket=bucket)
print(f"Bucket '{bucket}' eliminado")
