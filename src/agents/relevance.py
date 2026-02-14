import json
from typing import Optional, List
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.database import SessionLocal
from src.core.models import Content
from src.agents.base import BaseAgent
from src.core.config import Config

# --- LLM Client Setup ---
# Use LiteLLM or direct clients. For simplicity, let's use OpenAI/Gemini directly based on config.
# We'll prioritize OpenAI for now, falling back to Gemini if configured.
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
except ImportError:
    openai_client = None

try:
    import google.generativeai as genai
    if Config.GEMINI_API_KEY:
        genai.configure(api_key=Config.GEMINI_API_KEY)
except ImportError:
    pass

# --- Prompts ---
RELEVANCE_SYSTEM_PROMPT = """
You are an expert AI researcher and editor for a high-signal AI industry digest.
Your job is to evaluate if a piece of content is relevant to AI/GenAI professionals.

Input: Title, Abstract/Body
Output: JSON with `label`, `confidence_score` (0.0-1.0), and `reason`.

Allowed Labels:
- FOUNDATION_MODELS
- MULTIMODAL_AI
- AGENTIC_AI
- LLM_INFRASTRUCTURE
- AI_SAFETY_POLICY
- APPLIED_GENAI
- IRRELEVANT

Rules:
1. "IRRELEVANT" if it's general tech news, crypto, web3, or basic tutorials.
2. "IRRELEVANT" if confidence < 0.75.
3. Be strict. Only high-quality research or significant news.
"""

class RelevanceResult(BaseModel):
    label: str
    confidence_score: float
    reason: str

class RelevanceDecisionAgent(BaseAgent):
    """
    Scans DB for content with NULL relevance_label.
    Uses LLM to classify and score.
    """
    
    def _execute(self):
        self.logger.info("Starting Relevance Decision...")
        processed_count = 0
        
        with SessionLocal() as db:
            # 1. Select pending items
            pending_items = db.query(Content).filter(Content.relevance_label == None).limit(10).all() # Process in batches
            
            for item in pending_items:
                try:
                    decision = self.evaluate_relevance(item)
                    
                    item.relevance_label = decision.label
                    item.relevance_confidence = decision.confidence_score
                    item.relevance_reason = decision.reason
                    
                    self.logger.info(f"Classified {item.id} as {decision.label} ({decision.confidence_score})")
                    processed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to classify {item.id}: {e}")
            
            db.commit()
            
        self.logger.info(f"Relevance processing complete. Processed {processed_count} items.")
        return processed_count

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def evaluate_relevance(self, item: Content) -> RelevanceResult:
        """
        Calls LLM to evaluate relevance.
        """
        content_text = f"Title: {item.title}\nSource: {item.source}\nContent: {item.abstract_or_body[:2000]}"
        
        # Mock for verification/testing if no API key (prevent crash)
        if not Config.OPENAI_API_KEY and not Config.GEMINI_API_KEY:
            self.logger.warning("No LLM API Key found. Using mock decision.")
            return RelevanceResult(label="FOUNDATION_MODELS", confidence_score=0.9, reason="Mock decision (No API Key)")

        if openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4o" if Config.OPENAI_API_KEY else "gpt-3.5-turbo", # fallback or config
                messages=[
                    {"role": "system", "content": RELEVANCE_SYSTEM_PROMPT},
                    {"role": "user", "content": content_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            data = json.loads(response.choices[0].message.content)
            return RelevanceResult(**data)
        
        # Fallback to Gemini (omitted for brevity, assume OpenAI first for Plan)
        # In real impl, would have robust switcher.
        return RelevanceResult(label="IRRELEVANT", confidence_score=0.0, reason="No available LLM provider")

if __name__ == "__main__":
    agent = RelevanceDecisionAgent("test_relevance")
    agent.run()
