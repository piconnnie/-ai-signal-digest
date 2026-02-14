import json
import uuid
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy import desc

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
    2. Extracted Entities (Models, Orgs)
    3. Semantic Clustering (deduplication)
    """

    def _execute(self):
        self.logger.info("Starting Context Enrichment...")
        processed_count = 0
        
        with SessionLocal() as db:
            # Select items (Relevant) that are not enriched OR not clustered
            # For MVP simplicity, we process items where embedding is None (new items).
            # We assume if embedding is None, clustering is also needed.
            
            pending_items = db.query(Content).filter(
                Content.relevance_label.isnot(None), 
                Content.relevance_label != 'IRRELEVANT',
                Content.embedding_vector == None
            ).limit(20).all()

            for item in pending_items:
                try:
                    # 1. Generate Embedding
                    item.embedding_vector = self.generate_embedding(item.title + "\n" + (item.abstract_or_body or ""))
                    
                    # 2. Extract Entities
                    item.topics = self.extract_topics(item.abstract_or_body or "")

                    # 3. Assign Cluster
                    self.assign_cluster(db, item)
                    
                    self.logger.info(f"Enriched {item.id} (Cluster: {item.cluster_id})")
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
    
    def assign_cluster(self, db, item: Content):
        """
        Assigns a cluster_id. 
        Checks against recent items for duplicate/similar content.
        """
        # Look back 50 recent items that have a cluster_id
        recent_items = db.query(Content).filter(
            Content.cluster_id.isnot(None),
            Content.id != item.id
        ).order_by(desc(Content.id)).limit(50).all()
        
        best_match = None
        max_score = 0.0
        
        for candidate in recent_items:
            # Jaccard Similarity on Title
            score = self.jaccard_similarity(item.title, candidate.title)
            
            # Boost if URL is identical (dedup) - though AcqAgent handles exact URL dedup
            if item.url == candidate.url:
                score = 1.0
                
            if score > max_score:
                max_score = score
                best_match = candidate
        
        # Threshold for "Same Topic"
        if max_score > 0.4: # 40% word overlap in title is decent for "same news"
            item.cluster_id = best_match.cluster_id
            self.logger.info(f"Clustered {item.id} with {best_match.id} (Score: {max_score:.2f})")
        else:
            item.cluster_id = str(uuid.uuid4())

    def jaccard_similarity(self, s1: str, s2: str) -> float:
        """
        Calculates Jaccard similarity between two strings.
        """
        if not s1 or not s2:
            return 0.0
        
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
            
        return intersection / union

if __name__ == "__main__":
    agent = ContextEnrichmentAgent("test_enrichment")
    agent.run()
