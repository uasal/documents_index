import json
import os
from typing import Any

import sqlalchemy
from sqlalchemy.orm import close_all_sessions
from sqlalchemy.pool import NullPool

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('logger')

# [START cloudrun_user_auth_secrets]
def get_cred_config() -> dict[str, str]:
    """Retrieve Cloud SQL credentials stored in Secret Manager
    or default to environment variables.

    Returns:
        A dictionary with Cloud SQL credential values
    """
    secret = os.environ.get("CLOUD_SQL_CREDENTIALS_SECRET")
    if secret:
        return json.loads(secret)
    # [END cloudrun_user_auth_secrets]
    else:
        logger.info(
            "CLOUD_SQL_CREDENTIALS_SECRET env var not set. Defaulting to environment variables."
        )
        if "DB_USER" not in os.environ:
            raise Exception("DB_USER needs to be set.")

        if "DB_PASSWORD" not in os.environ:
            raise Exception("DB_PASSWORD needs to be set.")

        if "DB_NAME" not in os.environ:
            raise Exception("DB_NAME needs to be set.")

        if "CLOUD_SQL_CONNECTION_NAME" not in os.environ:
            raise Exception("CLOUD_SQL_CONNECTION_NAME needs to be set.")

        return {
            "DB_USER": os.environ["DB_USER"],
            "DB_PASSWORD": os.environ["DB_PASSWORD"],
            "DB_NAME": os.environ["DB_NAME"],
            "DB_HOST": os.environ.get("DB_HOST", None),
            "CLOUD_SQL_CONNECTION_NAME": os.environ["CLOUD_SQL_CONNECTION_NAME"],
        }


creds = get_cred_config()
db_user = creds["DB_USER"]
db_pass = creds["DB_PASSWORD"]
db_name = creds["DB_NAME"]
db_socket_dir = creds.get("DB_SOCKET_DIR", "/cloudsql")
cloud_sql_connection_name = creds["CLOUD_SQL_CONNECTION_NAME"]

DB_URI = f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}?unix_sock={db_socket_dir}/{cloud_sql_connection_name}/.s.PGSQL.5432"

