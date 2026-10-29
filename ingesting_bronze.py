import polars as pl 
import requests 
import boto3
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


s3_client = boto3.client(
    's3',
    endpoint_url='https://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    region_name='us-east-1')

def ensure_bucket_exists(bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logging.info(f"Bucket '{bucket_name}' already exists.")
    except s3_client.exceptions.NoSuchBucket:
        logging.info(f"Bucket '{bucket_name}' does not exist. Creating it...")
        s3_client.create_bucket(Bucket=bucket_name)
    
    for bucket in ['bronze', 'silver', 'gold']:
        ensure_bucket_exists(bucket)
        
# 2. Fetch data from BCB (Sistema Gerenciador de Séries Temporais)
# Serie 11 = Daily Selic Rate, Serie 433 = Monthly IPCA
def fetch_bcb_data(series_id):
    logging.info(f"Fetching data from {series_id}...")
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados?formato=json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

selic_data = fetch_bcb_data(11)
ipca_data = fetch_bcb_data(433)

# 3. Load into Polars DataFrames
df_selic = pl.DataFrame(selic_data)
df_ipca = pl.DataFrame(ipca_data)

# 4. Write directly to MinIO using Polars native S3 integration
storage_options = {
    "endpoint_url": "http://localhost:9000",
    "aws_access_key_id": "lakehouse_admin",
    "aws_secret_access_key": "lakehouse_password",
    "aws_region": "us-east-1",
}

logging.info("Writing Parquet files to Bronze layer...")

df_selic.write_parquet(
    "s3://bronze/bcb/selic_raw.parquet", 
    storage_options=storage_options
)

df_ipca.write_parquet(
    "s3://bronze/bcb/ipca_raw.parquet", 
    storage_options=storage_options
)

logging.info("Ingestion complete. Raw macroeconomic data landed in Lakehouse.")


