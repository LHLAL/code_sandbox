import sys
import io
import json
import subprocess
import os
import base64
from typing import Dict, Any, Optional
from .ast_checker import verify_code_safety

def restricted_exec_wrapper(code: str, args_b64: Optional[str], restricted_builtins_json: str):
    """
    注入到子进程中执行的包装器脚本
    支持 Base64 解码 args 并作为参数传递给 main(obj)
    """
    wrapper_script = f"""
import json
import io
import contextlib
import sys
import builtins
import base64

def run():
    code = {repr(code)}
    args_b64 = {repr(args_b64)}
    restricted_builtins = json.loads({repr(restricted_builtins_json)})
    
    # 获取并限制 builtins
    if hasattr(builtins, "__dict__"):
        safe_builtins = builtins.__dict__.copy()
    else:
        safe_builtins = builtins.copy()
        
    for b in restricted_builtins:
        safe_builtins.pop(b, None)
    
    global_scope = {{"__builtins__": safe_builtins}}
    local_scope = {{}}
    
    output_buffer = io.StringIO()
    error_msg = ""
    success = True
    
    try:
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
            # 1. 执行用户定义的代码（包括 main 函数定义）
            exec(code, global_scope, local_scope)
            
            # 2. 如果提供了 args，尝试解码并调用 main(obj)
            if args_b64:
                try:
                    # Base64 解码并转为 JSON 对象
                    decoded_bytes = base64.b64decode(args_b64)
                    obj = json.loads(decoded_bytes.decode('utf-8'))
                    
                    # 检查是否存在 main 函数并调用
                    if 'main' in local_scope and callable(local_scope['main']):
                        local_scope['main'](obj)
                    elif 'main' in global_scope and callable(global_scope['main']):
                        global_scope['main'](obj)
                    else:
                        # 如果没有 main 函数，代码已经在 exec 时跑过了
                        pass
                except Exception as e:
                    raise Exception(f"Failed to process args or call main: {{str(e)}}")
            
    except Exception as e:
        success = False
        error_msg = str(e)
    
    stdout_val = output_buffer.getvalue()
    
    sys.stdout.write("\\n---SANDBOX_OUTPUT_START---\\n")
    sys.stdout.write(json.dumps({{
        "success": success,
        "stdout": stdout_val,
        "error": error_msg
    }}))
    sys.stdout.write("\\n---SANDBOX_OUTPUT_END---\\n")

if __name__ == "__main__":
    run()
"""
    return wrapper_script

class PythonExecutor:
    def __init__(self, config):
        self.config = config

    def run(self, code: str, language: str, args: Optional[str] = None) -> Dict[str, Any]:
        # 1. AST 安全检查
        verify_code_safety(code, self.config.python_forbidden_modules)
        
        # 2. 确定 Python 解释器
        version_key = language.replace("python", "") if language.startswith("python") else language
        if not version_key:
            version_key = self.config.default_python_version
            
        python_exe = self.config.python_versions.get(version_key)
        if version_key == "3.11":
            python_exe = "python3"
            
        if not python_exe:
            raise Exception(f"Unsupported Python language/version: {language}")
        
        # 3. 准备执行包装器
        wrapper_code = restricted_exec_wrapper(
            code, 
            args,
            json.dumps(self.config.python_restricted_builtins)
        )
        
        try:
            process = subprocess.Popen(
                [python_exe, "-c", wrapper_code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=self.config.timeout)
            
            if "---SANDBOX_OUTPUT_START---" in stdout:
                parts = stdout.split("---SANDBOX_OUTPUT_START---")[1].split("---SANDBOX_OUTPUT_END---")
                result_json = parts[0].strip()
                return json.loads(result_json)
            else:
                return {
                    "success": False,
                    "stdout": stdout,
                    "error": stderr.strip() or "Failed to capture sandbox output"
                }
        except subprocess.TimeoutExpired:
            process.kill()
            return {"success": False, "stdout": "", "error": "Execution timed out"}
        except Exception as e:
            return {"success": False, "stdout": "", "error": str(e)}
