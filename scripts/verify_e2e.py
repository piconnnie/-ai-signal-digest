import logging
import sys
import time
from src.main import run_pipeline
from src.core.database import SessionLocal
from src.core.models import Content

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_system_state():
    """
    Checks DB state after pipeline run.
    """
    db = SessionLocal()
    
    # 1. Total Content
    total = db.query(Content).count()
    logger.info(f"Total Content Items: {total}")
    if total == 0:
        logger.error("FAILURE: No content found in DB.")
        return False

    # 2. RSS Ingestion Check
    rss_sources = ["OpenAI Blog", "Anthropic Blog", "Google AI Blog", "AWS Machine Learning"]
    rss_count = db.query(Content).filter(Content.source.in_(rss_sources)).count()
    logger.info(f"RSS Blog Items: {rss_count}")
    if rss_count == 0:
        logger.warning("WARNING: No RSS blog items found. Check internet or feed validity.")
        
    # 3. Clustering Check
    clustered = db.query(Content).filter(Content.cluster_id.isnot(None)).count()
    logger.info(f"Clustered Items: {clustered}")
    if clustered == 0 and total > 0:
        logger.warning("WARNING: No items clustered. Check EnrichmentAgent logic.")

    # 4. Critic Check (Validation Status)
    passed = db.query(Content).filter(Content.validation_status == 'PASS').count()
    failed = db.query(Content).filter(Content.validation_status == 'FAIL').count()
    logger.info(f"Critic Validation - PASS: {passed}, FAIL: {failed}")
    
    if passed == 0 and failed == 0:
        logger.warning("WARNING: No items validated by Critic. Check GuardrailAgent.")

    return True

def main():
    logger.info(">>> STARTING E2E VERIFICATION <<<")
    
    try:
        # Run the full pipeline
        run_pipeline()
        
        # Verify results
        if verify_system_state():
            logger.info(">>> E2E VERIFICATION PASSED <<<")
            sys.exit(0)
        else:
            logger.error(">>> E2E VERIFICATION FAILED <<<")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"E2E Execution Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
