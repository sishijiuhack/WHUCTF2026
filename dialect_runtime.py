import ast
import importlib
import io
import re
import traceback
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


TERMINATORS = ("。", "！", ".", "!")
BLOCKED_NAMES = {"open", "eval", "exec", "__import__", "compile"}
BLOCKED_ATTRS = {"system"}
ALLOWED_MODULES = {"builtins", "os", "math", "string", "re"}
SAFE_BUILTINS = {
    "print": print,
    "len": len,
    "range": range,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "enumerate": enumerate,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "type": type,
    "isinstance": isinstance,
    "Exception": Exception,
    "getattr": getattr,
}


class SandboxViolation(Exception):
    pass


class SafetyVisitor(ast.NodeVisitor):
    def visit_Import(self, node: ast.Import) -> None:
        raise SandboxViolation("禁止直接 import，请使用方言导入语句。")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        raise SandboxViolation("禁止直接 from import，请使用方言导入语句。")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in BLOCKED_NAMES:
            raise SandboxViolation(f"检测到危险函数名: {node.id}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in BLOCKED_ATTRS:
            raise SandboxViolation(f"检测到危险属性: {node.attr}")
        self.generic_visit(node)


@dataclass
class DialectSpec:
    name: str
    key: str


class DialectEngine:
    def __init__(self, spec: DialectSpec):
        self.spec = spec

    def _strip_line_end(self, line: str) -> str:
        line = line.rstrip()
        if not line:
            return line
        if line.endswith(TERMINATORS):
            return line[:-1].rstrip()
        # 粤语官方语法常见输出后缀：點樣先??
        if self.spec.key == "cantonese" and re.search(r"[點点]樣先\?*$", line):
            return line
        return line

    @staticmethod
    def _normalize_module_path(raw: str) -> str:
        mod = raw.strip()
        mod = mod.replace("咧", ".").replace("::", ".")
        mod = mod.strip(" .")
        return mod

    def _translate_import(self, line: str) -> Optional[List[str]]:
        # 兼容旧题面关键字
        m = re.match(r"^翘边\s+([a-zA-Z_][\w\.]*)(?:\s+做\s+([a-zA-Z_][\w]*))?$", line)
        if m:
            module_name = m.group(1)
            alias = m.group(2)
            bind_name = alias if alias else module_name.split(".")[-1]
            return [f"{bind_name} = __qiaobian__(\"{module_name}\")"]

        if self.spec.key in {"shanghai", "dongbei"}:
            # 上海: 阿庆，上 re。  东北: 翠花，上 re。
            m = re.match(r"^[^\s，,]+\s*[，,]\s*上\s+([a-zA-Z_][\w\.]*)$", line)
            if m:
                module_name = m.group(1)
                bind_name = module_name.split(".")[-1]
                return [f"{bind_name} = __qiaobian__(\"{module_name}\")"]

        if self.spec.key == "sichuan":
            # os咧path来给我扎起叫做os_path
            m = re.match(r"^(.+?)来给我扎起(?:叫做([a-zA-Z_][\w]*))?$", line)
            if m:
                module_name = self._normalize_module_path(m.group(1))
                alias = m.group(2)
                bind_name = alias if alias else module_name.split(".")[-1]
                if module_name:
                    return [f"{bind_name} = __qiaobian__(\"{module_name}\")"]

            # os咧path咧abspath出来给我扎起
            m = re.match(r"^(.+?)出来给我扎起(?:叫做([a-zA-Z_][\w]*))?$", line)
            if m:
                full_name = self._normalize_module_path(m.group(1))
                alias = m.group(2)
                parts = [p for p in full_name.split(".") if p]
                if len(parts) >= 2:
                    module_name = ".".join(parts[:-1])
                    attr_name = parts[-1]
                    bind_name = alias if alias else attr_name
                    return [
                        f"__mod_tmp = __qiaobian__(\"{module_name}\")",
                        f"{bind_name} = getattr(__mod_tmp, \"{attr_name}\")",
                    ]

        if self.spec.key == "cantonese":
            # 使下 py::os::* / 使下 py::math / 使下 os
            m = re.match(r"^使下\s+(.+?);?$", line)
            if m:
                raw = m.group(1).strip()
                if raw.startswith("py::"):
                    raw = raw[4:]

                modules: List[str] = []
                # py::{re::*, pandas}
                b = re.match(r"^\{(.+)\}$", raw)
                if b:
                    for item in b.group(1).split(","):
                        item = item.strip()
                        if item:
                            modules.append(item)
                else:
                    modules.append(raw)

                out: List[str] = []
                for mod in modules:
                    mod = mod.strip()
                    if mod.endswith("::*"):
                        mod = mod[:-3]
                    elif mod.endswith(".*"):
                        mod = mod[:-2]
                    mod = self._normalize_module_path(mod)
                    if not mod:
                        continue
                    bind_name = mod.split(".")[-1]
                    out.append(f"{bind_name} = __qiaobian__(\"{mod}\")")
                if out:
                    return out

        return None

    @staticmethod
    def _unwrap_wrapped_expr(expr: str) -> str:
        e = expr.strip()
        if e.startswith("|") and e.endswith("|") and len(e) >= 2:
            return e[1:-1].strip()
        return e

    def _translate_print(self, line: str) -> Optional[str]:
        # 兼容旧题面
        for kw in ("港港", "唠唠", "摆哈", "讲下"):
            if line.startswith(kw):
                rest = line[len(kw) :].strip()
                if rest.startswith("(") and rest.endswith(")"):
                    rest = rest[1:-1].strip()
                if not rest:
                    raise ValueError(f"{kw} 后需要一个表达式")
                return f"print({rest})"

        if self.spec.key == "shanghai":
            m = re.match(r"^嘎讪胡\s*[：:]\s*(.+)$", line)
            if m:
                expr = m.group(1).strip()
                if expr.startswith("\u767d\u76f8 "):
                    expr = expr[len("\u767d\u76f8 ") :].strip()
                return f"print({expr})"

        if self.spec.key == "dongbei":
            m = re.match(r"^(?:嘀咕|唠唠)\s*[：:]\s*(.+)$", line)
            if m:
                expr = m.group(1).strip()
                if expr.startswith("\u6574 "):
                    expr = expr[len("\u6574 ") :].strip()
                return f"print({expr})"

        if self.spec.key == "sichuan":
            m = re.match(r"^开腔[（(](.+)[）)]$", line)
            if m:
                return f"print({m.group(1).strip()})"

        if self.spec.key == "cantonese":
            m = re.match(r"^畀我睇下\s+(.+?)\s+[點点]樣先\?*$", line)
            if m:
                expr = self._unwrap_wrapped_expr(m.group(1))
                return f"print({expr})"

        return None

    def _translate_assign(self, line: str) -> Optional[str]:
        if self.spec.key == "dongbei":
            # 老王装 expr  →  老王 = expr
            m = re.match(r"^([a-zA-Z_\u4e00-\u9fff][\w\u4e00-\u9fff]*)\s*装\s*(.+)$", line)
            if m:
                return f"{m.group(1)} = {m.group(2).strip()}"

        if self.spec.key == "shanghai":
            # 阿庆毛估估是 expr  →  阿庆 = expr
            m = re.match(r"^([a-zA-Z_\u4e00-\u9fff][\w\u4e00-\u9fff]*)\s*毛估估是\s*(.+)$", line)
            if m:
                return f"{m.group(1)} = {m.group(2).strip()}"

        if self.spec.key == "sichuan":
            # 甲搁expr  →  甲 = expr
            m = re.match(r"^([a-zA-Z_\u4e00-\u9fff][\w\u4e00-\u9fff]*)\s*搁\s*(.+)$", line)
            if m:
                return f"{m.group(1)} = {m.group(2).strip()}"

        if self.spec.key == "cantonese":
            # 介紹返: |x| 係 expr  或  介紹返 |x| 係 expr  →  x = expr
            m = re.match(r"^介[紹绍]返\s*:?\s*\|?([a-zA-Z_\u4e00-\u9fff][\w\u4e00-\u9fff]*)\|?\s*[係系]\s*(.+)$", line)
            if m:
                return f"{m.group(1)} = {m.group(2).strip()}"

        return None

    def translate(self, code_lines: List[str]) -> str:
        out_lines: List[str] = []
        for raw in code_lines:
            stripped = self._strip_line_end(raw)
            if not stripped:
                continue

            translated_import = self._translate_import(stripped)
            if translated_import is not None:
                out_lines.extend(translated_import)
                continue

            translated_print = self._translate_print(stripped)
            if translated_print is not None:
                out_lines.append(translated_print)
                continue

            translated_assign = self._translate_assign(stripped)
            if translated_assign is not None:
                out_lines.append(translated_assign)
                continue

            out_lines.append(stripped)

        return "\n".join(out_lines)


def safe_import(module_name: str):
    if module_name not in ALLOWED_MODULES:
        raise SandboxViolation(f"不允许导入模块: {module_name}")
    return importlib.import_module(module_name)


class SessionRunner:
    def __init__(self, dialect: DialectSpec):
        self.engine = DialectEngine(dialect)
        self.globals: Dict[str, object] = {
            "__builtins__": SAFE_BUILTINS,
            "__name__": "__dialect_repl__",
        }

    def execute(self, code_lines: List[str]) -> Tuple[str, str]:
        try:
            py_src = self.engine.translate(code_lines)
            if not py_src.strip():
                return "", ""

            tree = ast.parse(py_src, mode="exec")
            SafetyVisitor().visit(tree)

            compiled = compile(tree, "<dialect>", "exec")
            exec_globals = dict(self.globals)
            exec_globals["__qiaobian__"] = safe_import
            stdout_io = io.StringIO()
            with redirect_stdout(stdout_io):
                exec(compiled, exec_globals, exec_globals)
            # 回写用户变量，但不保留 __qiaobian__
            exec_globals.pop("__qiaobian__", None)
            self.globals.update(exec_globals)
            return py_src, stdout_io.getvalue()
        except Exception as exc:
            msg = f"[RuntimeError] {exc}\n"
            if not isinstance(exc, (SandboxViolation, ValueError, SyntaxError)):
                msg += traceback.format_exc(limit=1)
            return "", msg


def get_dialects() -> Dict[str, DialectSpec]:
    return {
        "1": DialectSpec(name="上海话", key="shanghai"),
        "2": DialectSpec(name="东北话", key="dongbei"),
        "3": DialectSpec(name="四川话", key="sichuan"),
        "4": DialectSpec(name="粤语", key="cantonese"),
    }
