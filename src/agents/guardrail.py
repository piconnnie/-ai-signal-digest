import json
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

CRITIC_SYSTEM_PROMPT = """
You are a strict, cynical AI Editor and Fact-Checker. 
Your job is to validate a synthesized summary against the original content (or common knowledge if original is truncated).

Criteria:
1. Hallucination: Does the summary claim things not in the text?
2. Hype: Does the summary use excessive "game-changing", "revolutionary" language not supported by facts?
3. Safety: Is the content spam, scam, or irrelevant?

Input: Original Text (snippet), Summary Headline, Summary TLDR.
Output: JSON with:
- `score` (0-10): 10 is perfect, <7 is reject.
- `reason`: Short explanation.
- `flag`: One of ["OK", "HALLUCINATION", "HYPE", "SPAM"].
"""

class QualityGuardrailAgent(BaseAgent):
    """
    Validates synthesized insights before delivery.
    Now includes an LLM-based 'Critic' step.
    """

    def _execute(self):
        self.logger.info("Starting Quality Guardrail (Critic)...")
        processed_count = 0
        
        with SessionLocal() as db:
            # Select items that are Synthesized but Pending Validation
            items = db.query(Content).filter(
                Content.summary_headline.isnot(None),
                Content.validation_status == "PENDING"
            ).all()

            for item in items:
                try:
                    is_valid, reason = self.validate_content(item)
                    
                    if is_valid:
                        item.validation_status = "PASS"
                    else:
                        item.validation_status = "FAIL"
                        # Append critic reason to internal notes/logs if we had a field
                        # For now, just log and store in reason (if we had a validation_reason field)
                        self.logger.warning(f"Critic REJECTED {item.id}: {reason}")
                    
                    self.logger.info(f"Validated {item.id}: {item.validation_status}")
                    processed_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to validate {item.id}: {e}")
            
            db.commit()
            
        self.logger.info(f"Guardrail complete. Processed {processed_count} items.")
        return processed_count

    def validate_content(self, item: Content) -> (bool, str):
        """
        Validation rules:
        1. Base checks (length, source)
        2. LLM Critic Check
        """
        # 1. Base Checks
        if len(item.summary_headline or "") > 120:
            return False, "Headline too long"
            
        if not item.url:
            return False, "Missing source URL"
            
        # 2. LLM Critic
        if openai_client:
            try:
                score, reason = self.call_critic(item)
                if score < 7:
                    return False, f"Critic Score {score}/10: {reason}"
            except Exception as e:
                self.logger.error(f"Critic LLM failed: {e}")
                # Fallback: Pass if LLM fails? Or Fail? 
                # For safety, let's Fail if we heavily rely on it, or Pass if we treat it as optional.
                # Let's Pass but warn for MVP stability.
                self.logger.warning("Skipping Critic due to error.")
                
        return True, "OK"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def call_critic(self, item: Content):
        """
        Calls LLM to critique the content.
        """
        original_text = (item.abstract_or_body or "")[:3000]
        summary_text = f"Headline: {item.summary_headline}\nTLDR: {item.summary_tldr}\nHighlights: {item.summary_highlights}"
        
        prompt = f"Original Text:\n{original_text}\n\nproposed Summary:\n{summary_text}"
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        data = json.loads(response.choices[0].message.content)
        return data.get("score", 5), data.get("reason", "No reason provided")

if __name__ == "__main__":
    agent = QualityGuardrailAgent("test_guardrail")
    agent.run()
