import json
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.database import SessionLocal
from src.core.models import Content
from src.agents.base import BaseAgent
from src.core.config import Config

# --- Embeddings Client Setup ---
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
except ImportError:
    openai_client = None

class ContextEnrichmentAgent(BaseAgent):
    """
    Enriches content with:
    1. Embeddings (Vector)
    2. Extracted Entities (Models, Orgs - regex or LLM based)
    """

    def _execute(self):
        self.logger.info("Starting Context Enrichment...")
        processed_count = 0
        
        with SessionLocal() as db:
            # Select items that have been fetched but not enriched (embedding is None)
            # And optionally only those that are RELEVANT (to save cost)?
            # Strategy: Enrich everything to allow search, or only relevant?
            # Let's enrich only RELEVANT items for now to save cost, or all? 
            # If IRRELEVANT, we might not care.
            # But maybe we want to search irrelevant items too?
            # Let's stick to enriching items where relevance_label != 'IRRELEVANT' (or all if we want filtering later).
            # For efficiency: Enrich ONLY Relevant items.
            
            pending_items = db.query(Content).filter(
                Content.relevance_label.isnot(None), 
                Content.relevance_label != 'IRRELEVANT',
                Content.embedding_vector == None
            ).limit(20).all()

            for item in pending_items:
                try:
                    # 1. Generate Embedding
                    item.embedding_vector = self.generate_embedding(item.title + "\n" + (item.abstract_or_body or ""))
                    
                    # 2. Extract Entities (Simple keyword matching for now, or LLM)
                    # For MVP, let's use a placeholder list or simple extraction
                    item.topics = self.extract_topics(item.abstract_or_body or "")
                    
                    self.logger.info(f"Enriched {item.id}")
                    processed_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to enrich {item.id}: {e}")
            
            db.commit()
            
        self.logger.info(f"Enrichment processing complete. Processed {processed_count} items.")
        return processed_count

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector.
        """
        # Mock if no key
        if not openai_client:
            # return deterministic mock vector of dim 1536 (OpenAI standard)
            # Just return a small one for testing
            return [0.1] * 10 
            
        text = text[:8000] # Truncate to avoid token limits
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def extract_topics(self, text: str) -> List[str]:
        """
        Simple keyword extraction.
        """
        keywords = ["LLM", "Transformer", "Generative AI", "Reinforcement Learning", "Vision", "Agent", "Ethics"]
        found = [k for k in keywords if k.lower() in text.lower()]
        return found

if __name__ == "__main__":
    agent = ContextEnrichmentAgent("test_enrichment")
    agent.run()
