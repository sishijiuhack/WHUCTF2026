import ast
from dataclasses import dataclass
import re
import sys

@dataclass
class SecurityConfig:
    stdlib_allow: set[str]
    external_allow: set[str]
    builtins_deny: set[str]
    runner_env_deny: bool

FORMAT_FIELD_PATTERN = re.compile(r"\{([^}]*)\}")
# Security
BLOCKED_NAMES = {
    "__loader__",
    "__builtins__",
    "__globals__",
    "__spec__",
    "__name__",
}

BLOCKED_ATTRIBUTES = {
    # runtime attributes
    "__subclasses__",
    "__globals__",
    "__builtins__",
    "__traceback__",
    "tb_frame",
    "tb_next",
    "f_back",
    "f_globals",
    "f_locals",
    "f_code",
    "f_builtins",
    "__getattribute__",
    "__qualname__",
    "__module__",
    "gi_frame",
    "gi_code",
    "gi_yieldfrom",
    "cr_frame",
    "cr_code",
    "ag_frame",
    "ag_code",
    "__thisclass__",
    "__self_class__",
    "__objclass__",
    # introspection attributes
    "__base__",
    "__class__",
    "__bases__",
    "__code__",
    "__closure__",
    "__loader__",
    "__cached__",
    "__dict__",
    "__import__",
    "__mro__",
    "__init_subclass__",
    "__getattr__",
    "__setattr__",
    "__delattr__",
    "__self__",
    "__func__",
    "__wrapped__",
    "__annotations__",
    "__spec__",
}


# errors
ERROR_RELATIVE_IMPORT = "Relative imports are disallowed."
ERROR_STDLIB_DISALLOWED = "Import of standard library module '{module}' is disallowed. Allowed stdlib modules: {allowed}"
ERROR_EXTERNAL_DISALLOWED = "Import of external package '{module}' is disallowed. Allowed external packages: {allowed}"
ERROR_DANGEROUS_NAME = "Access to name '{name}' is disallowed, because it can be used to bypass security restrictions."
ERROR_DANGEROUS_ATTRIBUTE = "Access to attribute '{attr}' is disallowed, because it can be used to bypass security restrictions."
ERROR_DANGEROUS_STRING_PATTERN = "String pattern accessing '{attr}' is disallowed, because it can be used to bypass security restrictions."
ERROR_NAME_MANGLED_ATTRIBUTE = "Access to name-mangled attributes (pattern: _ClassName__attr) is disallowed for security reasons."
ERROR_DYNAMIC_IMPORT = (
    "Dynamic __import__() calls are not allowed for security reasons."
)
ERROR_MATCH_PATTERN_ATTRIBUTE = "Match pattern extracting attribute '{attr}' is disallowed, because it can be used to bypass security restrictions."
ERROR_WINDOWS_NOT_SUPPORTED = (
    "Error: This task runner is not supported on Windows. "
    "Please use a Unix-like system (Linux or macOS)."
)

def validate_module_import(
    module_path: str,
    security_config: SecurityConfig,
) -> tuple[bool, str | None]:
    stdlib_allow = security_config.stdlib_allow
    external_allow = security_config.external_allow

    module_name = module_path.split(".")[0]
    is_stdlib = module_name in sys.stdlib_module_names
    is_external = not is_stdlib

    if is_stdlib and ("*" in stdlib_allow or module_name in stdlib_allow):
        return (True, None)

    if is_external and ("*" in external_allow or module_name in external_allow):
        return (True, None)

    if is_stdlib:
        stdlib_allowed_str = ", ".join(sorted(stdlib_allow)) if stdlib_allow else "none"
        error_msg = ERROR_STDLIB_DISALLOWED.format(
            module=module_path, allowed=stdlib_allowed_str
        )
    else:
        external_allowed_str = (
            ", ".join(sorted(external_allow)) if external_allow else "none"
        )
        error_msg = ERROR_EXTERNAL_DISALLOWED.format(
            module=module_path, allowed=external_allowed_str
        )

    return (False, error_msg)

class SecurityValidator(ast.NodeVisitor):
    """AST visitor that enforces import allowlists and blocks dangerous attribute access."""

    def __init__(self, security_config: SecurityConfig):
        self.checked_modules: set[str] = set()
        self.violations: list[str] = []
        self.security_config = security_config

    # ========== Detection ==========

    def visit_Import(self, node: ast.Import) -> None:
        """Detect bare import statements (e.g., import os), including aliased (e.g., import numpy as np)."""

        for alias in node.names:
            module_name = alias.name
            self._validate_import(module_name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Detect from import statements (e.g., from os import path)."""

        if node.level > 0:
            self._add_violation(node.lineno, ERROR_RELATIVE_IMPORT)
        elif node.module:
            self._validate_import(node.module, node.lineno)

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in BLOCKED_NAMES:
            self._add_violation(node.lineno, ERROR_DANGEROUS_NAME.format(name=node.id))

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Detect access to unsafe attributes that could bypass security restrictions."""

        if node.attr in BLOCKED_ATTRIBUTES:
            self._add_violation(
                node.lineno, ERROR_DANGEROUS_ATTRIBUTE.format(attr=node.attr)
            )

        if node.attr.startswith("_") and "__" in node.attr:
            parts = node.attr.split("__", 1)
            if len(parts) == 2 and parts[0].startswith("_"):
                self._add_violation(node.lineno, ERROR_NAME_MANGLED_ATTRIBUTE)

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Detect dict access to blocked attributes, e.g. __builtins__['__spec__']"""

        is_builtins_access = (
            # __builtins__['__spec__']
            (
                isinstance(node.value, ast.Name)
                and node.value.id in {"__builtins__", "builtins"}
            )
            # obj.__builtins__['__spec__']
            or (
                isinstance(node.value, ast.Attribute)
                and node.value.attr in {"__builtins__", "builtins"}
            )
        )

        if (
            is_builtins_access
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            key = node.slice.value
            if key in BLOCKED_ATTRIBUTES:
                self._add_violation(
                    node.lineno, ERROR_DANGEROUS_ATTRIBUTE.format(attr=key)
                )

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        """Detect string constants containing dangerous format patterns."""

        if isinstance(node.value, str):
            self._check_format_string(node.value, node.lineno)

        self.generic_visit(node)

    def visit_MatchClass(self, node: ast.MatchClass) -> None:
        """Detect match patterns that extract blocked attributes, e.g. `case AttributeError(obj=x)`"""

        for attr in node.kwd_attrs:
            if attr in BLOCKED_ATTRIBUTES:
                self._add_violation(
                    node.lineno, ERROR_MATCH_PATTERN_ATTRIBUTE.format(attr=attr)
                )

        self.generic_visit(node)

    def _check_format_string(self, s: str, lineno: int) -> None:
        """Check if a string contains format patterns that access blocked attributes."""

        # escaped braces produce literal braces, not format fields
        s = s.replace("{{", "").replace("}}", "")

        for match in FORMAT_FIELD_PATTERN.finditer(s):
            field = match.group(1)

            # attribute access
            for attr_match in re.finditer(r"\.(\w+)", field):
                attr = attr_match.group(1)
                if attr in BLOCKED_ATTRIBUTES or attr in BLOCKED_NAMES:
                    self._add_violation(
                        lineno, ERROR_DANGEROUS_STRING_PATTERN.format(attr=attr)
                    )

            # subscript access
            for subscript_match in re.finditer(r"\[(['\"]?)(\w+)\1\]", field):
                key = subscript_match.group(2)
                if key in BLOCKED_ATTRIBUTES or key in BLOCKED_NAMES:
                    self._add_violation(
                        lineno, ERROR_DANGEROUS_STRING_PATTERN.format(attr=key)
                    )

    # ========== Validation ==========

    def _validate_import(self, module_path: str, lineno: int) -> None:
        """Validate that a module import is allowed based on allowlists. Also disallow relative imports."""

        if module_path.startswith("."):
            self._add_violation(lineno, ERROR_RELATIVE_IMPORT)
            return

        module_name = module_path.split(".")[0]  # e.g., os.path -> os

        if module_name in self.checked_modules:
            return

        self.checked_modules.add(module_name)

        is_allowed, error_msg = validate_module_import(
            module_path, self.security_config
        )

        if not is_allowed:
            assert error_msg is not None
            self._add_violation(lineno, error_msg)

    def _add_violation(self, lineno: int, message: str) -> None:
        self.violations.append(f"Line {lineno}: {message}")

class TaskAnalyzer:
    def __init__(self, security_config: SecurityConfig):
        self._security_config = security_config
        self._allowlists = (
            tuple(sorted(security_config.stdlib_allow)),
            tuple(sorted(security_config.external_allow)),
        )
        self._allow_all = (
            "*" in security_config.stdlib_allow
            and "*" in security_config.external_allow
        )

    def validate(self, code: str) -> None:

        tree = ast.parse(code)

        security_validator = SecurityValidator(self._security_config)
        security_validator.visit(tree)

        if security_validator.violations:
            self._raise_security_error(security_validator.violations)

    def _raise_security_error(self, violations) -> None:
        raise Exception("violations " + "\n".join(violations))