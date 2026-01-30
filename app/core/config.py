import yaml
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class SandboxConfig(BaseModel):
    port: int = 8000
    host: str = "0.0.0.0"
    workers: int = 4
    max_thread_pool_size: int = 100
    rate_limit: str = "100/minute"
    timeout: int = 5
    memory_limit: str = "128m"
    
    # Python versions mapping
    python_versions: Dict[str, str] = {
        "3.9": "python3.9",
        "3.10": "python3.10",
        "3.11": "python3.11"
    }
    default_python_version: str = "3.11"
    
    python_restricted_builtins: List[str] = ["open", "eval", "exec", "compile", "globals", "locals", "__import__"]
    python_forbidden_modules: List[str] = ["os", "sys", "subprocess", "shutil", "socket", "requests"]

    nodejs_enabled: bool = False

def load_config(config_path: str = "config/config.yaml") -> SandboxConfig:
    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
            return SandboxConfig(**data)
    except FileNotFoundError:
        return SandboxConfig()
