import config
import logging
from extract import extract_data
from transform import transform_data
from load import load_data
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_pipeline():

    raw_data = extract_data(config.API_URL)

    if raw_data:
        clean_df = transform_data(raw_data)
        if clean_df is not None and not clean_df.empty:
            load_data(clean_df)
            logger.info("SUCCESS : Pipeline Complete")
        else:
            logger.warning("Pipeline Halted: No Valid Data To Load")
    else:
        logger.error("Pipeline Halted : Extraction Failed")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        logger.exception("CRITICAL FATAIL ERROR : Pipeline Crashed!")
        sys.exit(1)