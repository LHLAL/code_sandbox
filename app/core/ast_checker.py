import ast
from typing import List, Set

class SecurityViolation(Exception):
    def __init__(self, message: str):
        self.message = message

class SandboxASTChecker(ast.NodeVisitor):
    def __init__(self, forbidden_modules: List[str]):
        self.forbidden_modules = set(forbidden_modules)
        self.errors = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split('.')[0] in self.forbidden_modules:
                self.errors.append(f"Forbidden import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split('.')[0] in self.forbidden_modules:
            self.errors.append(f"Forbidden import from: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        # Check for builtins bypass like __builtins__['eval']
        if isinstance(node.func, ast.Name):
            if node.func.id in ["eval", "exec", "compile", "__import__"]:
                self.errors.append(f"Forbidden function call: {node.func.id}")
        elif isinstance(node.func, ast.Attribute):
            # Check for things like os.system
            pass 
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Prevent access to dangerous attributes like __subclasses__
        if node.attr.startswith("__") and node.attr != "__init__":
            self.errors.append(f"Forbidden attribute access: {node.attr}")
        self.generic_visit(node)

def verify_code_safety(code: str, forbidden_modules: List[str]):
    try:
        tree = ast.parse(code)
        checker = SandboxASTChecker(forbidden_modules)
        checker.visit(tree)
        if checker.errors:
            raise SecurityViolation("; ".join(checker.errors))
    except SyntaxError as e:
        raise SecurityViolation(f"Syntax error: {str(e)}")
