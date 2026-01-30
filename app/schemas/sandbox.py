from pydantic import BaseModel
from typing import Dict, Any, Optional

class ExecuteRequest(BaseModel):
    code: str
    language: str = "python3.11"
    args: Optional[str] = None # Base64 encoded JSON string

class SandboxData(BaseModel):
    stdout: str
    error: str = ""

class ExecuteResponse(BaseModel):
    code: int
    message: str
    data: SandboxData
