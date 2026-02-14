import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.core.config import Config
from src.core.logger import setup_logger
from src.core.database import init_db

# Agents
from src.agents.acquisition import ContentAcquisitionAgent
from src.agents.relevance import RelevanceDecisionAgent
from src.agents.enrichment import ContextEnrichmentAgent
from src.agents.prioritization import PrioritizationAgent
from src.agents.synthesis import InsightSynthesisAgent
from src.agents.guardrail import QualityGuardrailAgent
from src.agents.delivery import DeliveryAgent

logger = setup_logger("orchestrator")

def run_pipeline():
    """
    Execute the full signal digest pipeline.
    """
    logger.info(">>> Starting Pipeline Execution <<<")
    
    # 1. Acquisition
    acq_agent = ContentAcquisitionAgent("acquisition")
    new_items = acq_agent.run()
    
    if new_items == 0:
        logger.info("No new content. Skipping remaining steps (or maybe we process pending?).")
        # For robustness, we should continue to process pending items even if no NEW items fetched.
        # But for efficiency, maybe skip? 
        # Let's continues, as Relevance might have pending items from previous failed runs.
    
    # 2. Relevance
    rel_agent = RelevanceDecisionAgent("relevance")
    rel_agent.run()
    
    # 3. Enrichment
    enr_agent = ContextEnrichmentAgent("enrichment")
    enr_agent.run()
    
    # 4. Prioritization
    prio_agent = PrioritizationAgent("prioritization")
    prio_agent.run()
    
    # 5. Synthesis
    syn_agent = InsightSynthesisAgent("synthesis")
    syn_agent.run()
    
    # 6. Guardrail
    guard_agent = QualityGuardrailAgent("guardrail")
    guard_agent.run()
    
    # 7. Delivery
    del_agent = DeliveryAgent("delivery")
    del_agent.run()
    
    logger.info(">>> Pipeline Execution Complete <<<")

def main():
    # Ensure DB exists
    init_db()
    
    if Config.DRY_RUN:
        logger.info("Running in DRY_RUN mode. One-off execution.")
        run_pipeline()
        return

    # Scheduler Setup
    scheduler = BlockingScheduler()
    
    # Schedule: Run daily at 9:00 AM
    scheduler.add_job(
        run_pipeline,
        trigger=CronTrigger(hour=9, minute=0),
        id='signal_digest_pipeline',
        name='Run Signal Digest Pipeline',
        replace_existing=True
    )
    
    logger.info("Scheduler started. Press Ctrl+C to exit.")
    
    try:
        # Run once immediately on startup?
        run_pipeline() 
        
        # Start blocking loop
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()
