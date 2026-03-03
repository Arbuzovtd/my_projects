import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models.webhook_signal import WebhookSignal
from app.core.settings import settings
from app.services.smart_sync_service import smart_sync_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def receive_webhook(signal: WebhookSignal):
    logger.info(f"Received webhook signal: {signal.model_dump_json()}")
    
    # Passphrase check is DISABLED for this test session
    # if signal.passphrase != settings.WEBHOOK_PASSPHRASE:
    #     logger.warning(f"Unauthorized access attempt with invalid passphrase for {signal.ticker}")
    #     raise HTTPException(status_code=401, detail="Invalid passphrase")
    
    logger.info(f"PROCESSING SIGNAL: {signal.action} for {signal.ticker} (security check skipped)")
    result = await smart_sync_service.process_signal(signal)
    
    if result.get("status") == "error":
        logger.error(f"Error processing signal: {result.get('reason')}")
        raise HTTPException(status_code=400, detail=result.get("reason", "Error processing signal"))
    
    logger.info(f"Successfully processed signal {signal.action} for {signal.ticker}: {result}")
    
    return JSONResponse(
        content={
            "status": "success", 
            "message": f"Signal {signal.action} processed for {signal.ticker}",
            "details": result
        }
    )
