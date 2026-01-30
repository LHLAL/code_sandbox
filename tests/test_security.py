import pytest
from app.core.ast_checker import verify_code_safety, SecurityViolation
from app.core.executor import PythonExecutor
from app.core.config import SandboxConfig

config = SandboxConfig()
executor = PythonExecutor(config)

def test_ast_forbidden_import():
    code = "import os\nos.system('ls')"
    with pytest.raises(SecurityViolation) as excinfo:
        verify_code_safety(code, config.python_forbidden_modules)
    assert "Forbidden import: os" in str(excinfo.value)

def test_runtime_builtin_restriction():
    code = "open('test.txt', 'w')"
    result = executor.run(code, "python3.11")
    assert result["success"] is False
    assert "name 'open' is not defined" in result["error"]

def test_successful_execution_with_main():
    code = "def main(obj): print(f'Data: {obj}')"
    import base64
    import json
    args = base64.b64encode(json.dumps("test_data").encode()).decode()
    result = executor.run(code, "python3.11", args=args)
    assert result["success"] is True
    assert "Data: test_data" in result["stdout"]
