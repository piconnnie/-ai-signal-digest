from src.core.database import SessionLocal
from src.core.models import Content
from src.agents.base import BaseAgent

class QualityGuardrailAgent(BaseAgent):
    """
    Validates synthesized insights before delivery.
    """

    def _execute(self):
        self.logger.info("Starting Quality Guardrail...")
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
                        self.logger.warning(f"Validation FAILED for {item.id}: {reason}")
                    
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
        1. Headline length <= 120 chars
        2. Source URL present
        3. No 'As an AI' language (simple check)
        """
        # 1. Length
        if len(item.summary_headline or "") > 120:
            return False, "Headline too long"
            
        # 2. Source
        if not item.url:
            return False, "Missing source URL"
            
        # 3. AI boilerplate
        forbidden = ["As an AI", "I cannot", "knowledge cutoff"]
        full_text = (item.summary_tldr or "") + " " + " ".join(item.summary_highlights or [])
        for phrase in forbidden:
            if phrase.lower() in full_text.lower():
                return False, f"Contains forbidden phrase: {phrase}"
                
        return True, "OK"

if __name__ == "__main__":
    agent = QualityGuardrailAgent("test_guardrail")
    agent.run()
