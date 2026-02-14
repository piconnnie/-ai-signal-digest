import json
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.database import SessionLocal
from src.core.models import Content
from src.agents.base import BaseAgent
from src.core.config import Config

# --- LLM Client ---
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
except ImportError:
    openai_client = None

SYNTHESIS_SYSTEM_PROMPT = """
You are an expert AI editor.
Synthesize the provided content into a concise insight digest for WhatsApp.

Input: Title, Body
Output Format: JSON with:
- `headline` (max 120 chars, catchy but factual)
- `tldr` (max 3 sentences)
- `highlights` (list of 3-5 strings)
- `why_it_matters` (1 sentence)

Style:
- Neutral, factual, high-signal.
- No jargon unless necessary.
- No emojis through this prompt (added later).
"""

class InsightSynthesisAgent(BaseAgent):
    """
    Takes Top N prioritized items and synthesizes them.
    """

    def _execute(self, limit=5):
        self.logger.info("Starting Insight Synthesis...")
        processed_count = 0
        
        with SessionLocal() as db:
            # Select top prioritized items that haven't been synthesized
            # i.e., priority_score > 0 and summary_headline is NULL
            
            items = db.query(Content).filter(
                Content.priority_score > 0,
                Content.summary_headline == None
            ).order_by(Content.priority_score.desc()).limit(limit).all()

            for item in items:
                try:
                    summary = self.generate_summary(item)
                    
                    item.summary_headline = summary.headline
                    item.summary_tldr = summary.tldr
                    item.summary_highlights = summary.highlights
                    item.summary_why_matters = summary.why_it_matters
                    item.validation_status = "PENDING"
                    
                    self.logger.info(f"Synthesized {item.id}: {item.summary_headline}")
                    processed_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to synthesize {item.id}: {e}")
            
            db.commit()
            
        self.logger.info(f"Synthesis complete. Generated {processed_count} summaries.")
        return processed_count

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_summary(self, item: Content):
        content_text = f"Title: {item.title}\nBody: {item.abstract_or_body[:4000]}"
        
        class SummaryResult:
            def __init__(self, headline, tldr, highlights, why_it_matters):
                self.headline = headline
                self.tldr = tldr
                self.highlights = highlights
                self.why_it_matters = why_it_matters

        # Mock if no key
        if not openai_client:
            return SummaryResult(
                headline=f"Summary of {item.title[:20]}...",
                tldr="This is a mock summary because no API key is present.",
                highlights=["Point 1", "Point 2"],
                why_it_matters="It matters because we need to test."
            )

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": content_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        data = json.loads(response.choices[0].message.content)
        return SummaryResult(
            headline=data.get("headline", ""),
            tldr=data.get("tldr", ""),
            highlights=data.get("highlights", []),
            why_it_matters=data.get("why_it_matters", "")
        )

if __name__ == "__main__":
    agent = InsightSynthesisAgent("test_synthesis")
    agent.run()
