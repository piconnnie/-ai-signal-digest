from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.database import SessionLocal
from src.core.models import Content
from src.agents.base import BaseAgent
from src.core.config import Config

# --- Twilio Client ---
try:
    from twilio.rest import Client
    twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN) if Config.TWILIO_ACCOUNT_SID else None
except ImportError:
    twilio_client = None

class DeliveryAgent(BaseAgent):
    """
    Delivers validated insights via WhatsApp.
    """

    def _execute(self, target_phone=None):
        self.logger.info("Starting Delivery...")
        processed_count = 0
        
        with SessionLocal() as db:
            # Select PASS validation items that haven't been delivered
            items = db.query(Content).filter(
                Content.validation_status == "PASS",
                Content.delivery_status == "PENDING"
            ).all()

            if not items:
                self.logger.info("No items to deliver.")
                return 0

            # Group items into a single digest? Or send individually?
            # Project req: "Continuous delivery" vs "Daily digest".
            # Requirement says "Daily digest readable in <= 2 minutes".
            # So we should probably compile them?
            # For this MVP agent, let's send them one by one or compile all pending into one message.
            # WhatsApp limit is 1600 chars (Twilio) or 1024 chars per message (Project Req).
            # Let's try to compile.
            
            # Simple approach: Delivery loop
            # Real impl would check User preferences. Here we assume a single broadcast list or just log it.
            # We will simulate delivery to Config.TWILIO_FROM_NUMBER or a test number.
            
            # Mock "User" target
            target = target_phone or "+15555555555" 

            digest_body = "*AI Signal Digest*\n\n"
            sent_ids = []
            
            for item in items:
                entry = f"*{item.summary_headline}*\n{item.summary_tldr}\n_{item.url}_\n\n"
                if len(digest_body) + len(entry) > 1000:
                    # Send current batch
                    self.send_whatsapp(digest_body, target)
                    digest_body = "*AI Signal Digest (Cont.)*\n\n"
                
                digest_body += entry
                sent_ids.append(item.id)
            
            # Send remaining
            if sent_ids:
                self.send_whatsapp(digest_body, target)
                
                # Update status
                for item in items:
                    if item.id in sent_ids:
                        item.delivery_status = "SENT"
                
                processed_count = len(sent_ids)
                db.commit()
            
        self.logger.info(f"Delivery complete. Sent {processed_count} items.")
        return processed_count

    def send_whatsapp(self, body, to):
        if Config.DRY_RUN:
            self.logger.info(f"[DRY RUN] Would send to {to}:\n{body}")
            return
            
        if not twilio_client:
            self.logger.warning(f"[MOCK] No Twilio Client. Sending to {to}:\n{body}")
            return

        try:
            message = twilio_client.messages.create(
                from_=Config.TWILIO_FROM_NUMBER,
                body=body,
                to=f"whatsapp:{to}"
            )
            self.logger.info(f"Sent message SID: {message.sid}")
        except Exception as e:
            self.logger.error(f"Twilio Send Failed: {e}")
            raise e

if __name__ == "__main__":
    agent = DeliveryAgent("test_delivery")
    agent.run()
