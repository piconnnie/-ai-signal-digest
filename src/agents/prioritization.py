from datetime import datetime
from sqlalchemy import desc
from src.core.database import SessionLocal
from src.core.models import Content
from src.agents.base import BaseAgent

class PrioritizationAgent(BaseAgent):
    """
    Ranks enriched content to select top items for synthesis.
    Simple heuristic ranking for MVP.
    """

    def _execute(self):
        self.logger.info("Starting Prioritization...")
        processed_count = 0
        
        with SessionLocal() as db:
            # Select enriched items that haven't been prioritized/synthesized yet (or re-prioritize pending)
            # We want items causing 'PENDING' synthesis
            # Let's say we prioritize items that are RELEVANT and have topics/embeddings
            
            items = db.query(Content).filter(
                Content.relevance_label.isnot(None),
                Content.relevance_label != 'IRRELEVANT',
                Content.priority_score == 0.0 # Not yet ranked
            ).all()

            for item in items:
                try:
                    score = self.calculate_priority(item)
                    item.priority_score = score
                    
                    self.logger.info(f"Prioritized {item.id}: Score {score}")
                    processed_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to prioritize {item.id}: {e}")
            
            db.commit()
            
        self.logger.info(f"Prioritization complete. Ranked {processed_count} items.")
        return processed_count

    def calculate_priority(self, item: Content) -> float:
        """
        Heuristic scoring:
        - Base: Relevance Confidence (0.75 - 1.0)
        - News vs Research bias?
        - Recency boost?
        """
        score = item.relevance_confidence or 0.0
        
        # Boost for "FOUNDATION_MODELS" or "AGENTIC_AI"
        if item.relevance_label in ["FOUNDATION_MODELS", "AGENTIC_AI"]:
            score += 0.1
            
        # Boost for very recent (last 24h)
        delta = datetime.utcnow() - item.published_at
        if delta.days < 1:
            score += 0.05
            
        return round(score, 3)

if __name__ == "__main__":
    agent = PrioritizationAgent("test_prioritization")
    agent.run()
