import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
  "s3",
  "us-west-1",
  aws_access_key_id=os.environ["AWS_ACCESS_KEY"],
  aws_secret_access_key=os.environ["AWS_ACCESS_SECRET"],
)

s3.upload_file("img1.jpg", os.environ["S3_BUCKET_NAME"], "img1.jpg")