from datetime import datetime, timedelta
import logging
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import polars as pl
import requests
from generate_env import ensure_env_file, mask_secret

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 1. Load or generate credentials from .env using `secrets` and `dotenv`
env_path = ensure_env_file()
load_dotenv(dotenv_path=env_path)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.environ["MINIO_ROOT_USER"]
MINIO_SECRET_KEY = os.environ["MINIO_ROOT_PASSWORD"]
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

logging.info(
    f"Connecting to MinIO at {MINIO_ENDPOINT} with user {mask_secret(MINIO_ACCESS_KEY)}"
)

s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name=AWS_REGION,
)

def ensure_bucket_exists(bucket_name: str) -> None:
    """Check if an S3 bucket exists, and create it if it doesn't."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logging.info(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchBucket"):
            logging.info(f"Bucket '{bucket_name}' does not exist. Creating it...")
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            raise

# 2. Fetch data from BCB (Sistema Gerenciador de Séries Temporais)
# Serie 11 = Daily Selic Rate, Serie 433 = Monthly IPCA
BCB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

def fetch_bcb_data(
    series_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
):
    if end_date is None:
        end_dt = datetime.now()
        end_date = end_dt.strftime("%d/%m/%Y")
    else:
        end_dt = datetime.strptime(end_date, "%d/%m/%Y")

    if start_date is None:
        # BCB API requires dataInicial/dataFinal with a max 10-year window for daily series
        start_dt = end_dt - timedelta(days=365 * 9)
        start_date = start_dt.strftime("%d/%m/%Y")

    logging.info(f"Fetching data from series {series_id} ({start_date} to {end_date})...")
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados"
        f"?formato=json&dataInicial={start_date}&dataFinal={end_date}"
    )
    response = requests.get(url, headers=BCB_HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()

def main():
    # Ensure all required Lakehouse buckets exist
    for bucket in ["bronze", "silver", "gold"]:
        ensure_bucket_exists(bucket)

    # Fetch BCB macroeconomic series
    selic_data = fetch_bcb_data(11)
    ipca_data = fetch_bcb_data(433)

    # Load into Polars DataFrames
    df_selic = pl.DataFrame(selic_data)
    df_ipca = pl.DataFrame(ipca_data)

    # Configure Polars S3 storage options
    # Note: aws_allow_http='true' is mandatory for local plain HTTP MinIO endpoints
    storage_options = {
        "aws_endpoint_url": MINIO_ENDPOINT,
        "endpoint_url": MINIO_ENDPOINT,
        "aws_access_key_id": MINIO_ACCESS_KEY,
        "aws_secret_access_key": MINIO_SECRET_KEY,
        "aws_region": AWS_REGION,
        "aws_allow_http": "true",
    }

    logging.info("Writing Parquet files to Bronze layer...")

    df_selic.write_parquet(
        "s3://bronze/bcb/selic_raw.parquet",
        storage_options=storage_options,
    )

    df_ipca.write_parquet(
        "s3://bronze/bcb/ipca_raw.parquet",
        storage_options=storage_options,
    )

    logging.info("Ingestion complete. Raw macroeconomic data landed in Lakehouse.")

if __name__ == "__main__":
    main()



