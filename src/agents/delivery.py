from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.database import SessionLocal
from src.core.models import Content, User
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

            # Get all subscribed users
            users = db.query(User).filter(User.opt_in_status == True).all()
            if not users:
                self.logger.info("No subscribed users found.")
                # We still mark items as delivered? No, maybe keep them pending until we hava users?
                # Or just mark them as sent to "ghosts" so they don't pile up?
                # Let's log and return.
                return 0

            # Prepare Digest Body
            digest_body = "*AI Signal Digest*\n\n"
            sent_ids = []
            
            # Construct the single digest from all items
            # Note: This constructs ONE digest for ALL users. 
            # Personalization would require per-user construction.
            
            temp_body = digest_body
            for item in items:
                entry = f"*{item.summary_headline}*\n{item.summary_tldr}\n_{item.url}_\n\n"
                if len(temp_body) + len(entry) > 1000:
                    # If we exceed limit, we would need to split. 
                    # For MVP, let's just truncate or stop adding items to this batch?
                    # Or send multiple messages?
                    # Let's send multiple messages if needed.
                    pass 
                temp_body += entry
                sent_ids.append(item.id)
            
            # For MVP, let's just blast the full body (split by Twilio if needed, or we split)
            # Simple splitter:
            messages_to_send = []
            current_msg = "*AI Signal Digest*\n\n"
            
            for item in items:
                entry = f"*{item.summary_headline}*\n{item.summary_tldr}\n_{item.url}_\n\n"
                if len(current_msg) + len(entry) > 1500: # Safety margin for Twilio
                     messages_to_send.append(current_msg)
                     current_msg = "*AI Signal Digest (Cont.)*\n\n" + entry
                else:
                    current_msg += entry
            
            if current_msg:
                messages_to_send.append(current_msg)

            # Broadcast to all users
            for user in users:
                self.logger.info(f"Sending digest to {user.phone_number}...")
                for msg in messages_to_send:
                    self.send_whatsapp(msg, user.phone_number)
            
            # Mark items as SENT
            for item in items:
                item.delivery_status = "SENT"
            
            processed_count = len(items)
            db.commit()
            
        self.logger.info(f"Delivery complete. Sent {processed_count} items to {len(users)} users.")
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
