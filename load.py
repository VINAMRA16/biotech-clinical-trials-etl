import os 
from dotenv import load_dotenv
from sqlalchemy import create_engine,text
import urllib.parse
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def load_data(df):

    db_user = os.getenv("DB_USER")
    db_host = os.getenv("DB_HOST")
    db_pass = os.getenv("DB_PASS")

    safe_pass = urllib.parse.quote_plus(db_pass)

    server_engine = create_engine(f"mysql+mysqlconnector://{db_user}:{safe_pass}@{db_host}/")

    with server_engine.connect() as conn:
        conn.execute(text("CREATE DATABASE IF NOT EXISTS biotech_vault"))

    vault_engine = create_engine(f"mysql+mysqlconnector://{db_user}:{safe_pass}@{db_host}/biotech_vault")

    df.to_sql(
        name="major_clinical_trials",
        con=vault_engine,
        if_exists="replace",
        index=False
    )

    logger.info("SUCCESSFULLY Loaded Data Into MySQL Database")
