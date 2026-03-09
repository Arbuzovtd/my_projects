import hmac
import hashlib
import json
import logging
from urllib.parse import parse_qsl
from fastapi import Header, HTTPException, Depends
from app.core.settings import settings

logger = logging.getLogger(__name__)

def verify_telegram_webapp_data(x_tg_data: str = Header(None)):
    """
    Verifies the data sent by the Telegram Web App.
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    if not x_tg_data:
        logger.warning("No Telegram init data provided in headers")
        raise HTTPException(status_code=401, detail="Unauthorized: No init data")

    try:
        # 1. Parse the query string
        vals = dict(parse_qsl(x_tg_data))
        hash_val = vals.pop('hash', None)
        
        # 2. Sort keys alphabetically
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(vals.items())])
        
        # 3. Create secret key
        # HMAC-SHA256(data_check_string, HMAC-SHA256("WebAppData", bot_token))
        secret_key = hmac.new(b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        # 4. Compare hashes
        if calculated_hash != hash_val:
            logger.error("Telegram hash mismatch! Potential unauthorized access attempt.")
            raise HTTPException(status_code=403, detail="Forbidden: Invalid hash")

        # 5. Check if User ID is in allowed list (TELEGRAM_CHAT_ID)
        user_data = json.loads(vals.get('user', '{}'))
        user_id = str(user_data.get('id'))
        
        allowed_ids = [id.strip() for id in settings.TELEGRAM_CHAT_ID.split(",") if id.strip()]
        
        if user_id not in allowed_ids:
            logger.warning(f"User {user_id} is not in allowed list: {allowed_ids}")
            raise HTTPException(status_code=403, detail="Forbidden: User not allowed")

        return user_id

    except Exception as e:
        logger.error(f"Error validating Telegram data: {e}")
        raise HTTPException(status_code=403, detail=f"Forbidden: {str(e)}")
