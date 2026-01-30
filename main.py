import uvicorn
from fastapi import FastAPI
from app.api.router import router
from app.core.config import load_config
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from concurrent.futures import ThreadPoolExecutor
import asyncio
import os

config_path = os.getenv("SANDBOX_CONFIG_PATH", "config/config.yaml")
config = load_config(config_path)

app = FastAPI(title="Manus Safe Sandbox")
app.include_router(router)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return _rate_limit_exceeded_handler(request, exc)

if __name__ == "__main__":
    # Note: When running with uvicorn workers > 1, the thread pool config should be inside the worker init
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        workers=config.workers,
        log_level="info"
    )
