---
name: whatsapp-delivery
description: Patterns for sending WhatsApp messages via Twilio API.
---

# WhatsApp Delivery (Twilio)

## Core Library
- **Twilio**: Official Python helper library.

## Configuration
Requires `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_WHATSAPP_NUMBER`.

## Sending Messages

```python
from twilio.rest import Client
import os

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

message = client.messages.create(
    from_='whatsapp:+14155238886', # Your Sandbox or Business Number
    body='Your appointment is coming up on July 21 at 3PM',
    to='whatsapp:+15005550006'
)

print(message.sid)
```

## Content Constraints
- **Length**: Limit to 1600 chars (Twilio limit) or 1024 chars (Project Requirement).
- **Template Messages**: Required if > 24 hours since last user message.
  - Template structure must match APPROVED templates in Twilio console.
  - Variable replacement ({{1}}, {{2}}).

## Error Handling
- Wrap in `try-except` to catch `TwilioRestException`.
- Log `message.sid` and `message.status`.
