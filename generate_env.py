import logging
import os
from pathlib import Path
import secrets
from dotenv import load_dotenv, set_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ENV_PATH = Path(__file__).resolve().parent / ".env"


def mask_secret(value: str, visible: int = 2) -> str:
    """Mask a secret string for safe logging (e.g., 'ab********yz')."""
    if not value or len(value) <= visible * 2:
        return "********"
    return f"{value[:visible]}{'*' * 8}{value[-visible:]}"


def ensure_env_file(force_regenerate: bool = False) -> Path:
    """Generate and persist all project credentials in .env using `secrets` and `dotenv`."""
    if not ENV_PATH.exists():
        ENV_PATH.touch(mode=0o600)

    load_dotenv(dotenv_path=ENV_PATH)

    # Non-secret configuration defaults
    defaults = {
        "MINIO_ENDPOINT": "http://localhost:9000",
        "MINIO_ENDPOINT_HOST": "localhost:9000",
        "AWS_REGION": "us-east-1",
        "POSTGRES_USER": "airflow",
        "POSTGRES_DB": "quantum_finance",
    }
    for key, default_val in defaults.items():
        if not os.getenv(key):
            set_key(str(ENV_PATH), key, default_val, quote_mode="never")

    # MinIO Root User
    minio_user = os.getenv("MINIO_ROOT_USER")
    if force_regenerate or not minio_user:
        minio_user = f"qf_admin_{secrets.token_hex(4)}"
        set_key(str(ENV_PATH), "MINIO_ROOT_USER", minio_user, quote_mode="never")
        logging.info(f"Generated MINIO_ROOT_USER: {mask_secret(minio_user)}")
    else:
        logging.info(f"Loaded MINIO_ROOT_USER: {mask_secret(minio_user)}")

    # MinIO Root Password
    minio_password = os.getenv("MINIO_ROOT_PASSWORD")
    if force_regenerate or not minio_password:
        minio_password = secrets.token_urlsafe(24)
        set_key(str(ENV_PATH), "MINIO_ROOT_PASSWORD", minio_password, quote_mode="never")
        logging.info(f"Generated MINIO_ROOT_PASSWORD: {mask_secret(minio_password)}")
    else:
        logging.info(f"Loaded MINIO_ROOT_PASSWORD: {mask_secret(minio_password)}")

    # Postgres Password
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    if force_regenerate or not postgres_password:
        postgres_password = secrets.token_urlsafe(24)
        set_key(str(ENV_PATH), "POSTGRES_PASSWORD", postgres_password, quote_mode="never")
        logging.info(f"Generated POSTGRES_PASSWORD: {mask_secret(postgres_password)}")
    else:
        logging.info(f"Loaded POSTGRES_PASSWORD: {mask_secret(postgres_password)}")

    # Reload environment variables after updates
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return ENV_PATH


if __name__ == "__main__":
    ensure_env_file()
    logging.info("All credentials securely stored in .env (masked from GitHub via .gitignore).")
