from fastapi import APIRouter, HTTPException, Request
from ..schemas.sandbox import ExecuteRequest, ExecuteResponse, SandboxData
from ..core.executor import PythonExecutor
from ..core.config import load_config
from slowapi import Limiter
from slowapi.util import get_remote_address
import asyncio
import os

router = APIRouter()
config_path = os.getenv("SANDBOX_CONFIG_PATH", "config/config.yaml")
config = load_config(config_path)
limiter = Limiter(key_func=get_remote_address)
executor = PythonExecutor(config)

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Sandbox is healthy"}

@router.post("/v1/sandbox/run", response_model=ExecuteResponse)
@limiter.limit(config.rate_limit)
async def execute_code(request: Request, exec_req: ExecuteRequest):
    if exec_req.language.startswith("python"):
        try:
            loop = asyncio.get_event_loop()
            raw_result = await loop.run_in_executor(
                None, 
                executor.run, 
                exec_req.code, 
                exec_req.language,
                exec_req.args
            )
            
            return ExecuteResponse(
                code=0 if raw_result["success"] else 1,
                message="success" if raw_result["success"] else "execution error",
                data=SandboxData(
                    stdout=raw_result["stdout"].strip(),
                    error=raw_result["error"] or ""
                )
            )
        except Exception as e:
            return ExecuteResponse(
                code=1,
                message="system error",
                data=SandboxData(stdout="", error=str(e))
            )
    elif exec_req.language == "nodejs":
        return ExecuteResponse(
            code=1,
            message="unsupported language",
            data=SandboxData(stdout="", error="Node.js sandbox is not implemented yet (placeholder)")
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")
