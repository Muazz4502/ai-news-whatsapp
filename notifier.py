import logging
import time

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, TWILIO_TO

logger = logging.getLogger(__name__)


def send_whatsapp(message: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    Returns True on success, False on failure.
    """
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    backoff = 2

    for attempt in range(3):
        try:
            msg = client.messages.create(
                body=message,
                from_=TWILIO_FROM,
                to=TWILIO_TO,
            )
            logger.info(f"WhatsApp message sent successfully. SID: {msg.sid}")
            return True

        except TwilioRestException as e:
            if e.status == 429:
                logger.warning(f"Twilio rate limit (attempt {attempt + 1}). Backing off {backoff}s.")
                time.sleep(backoff)
                backoff *= 2
            else:
                logger.error(f"Twilio error [{e.status}]: {e.msg}")
                return False

    logger.error("Twilio: exhausted retries after rate limiting.")
    return False
