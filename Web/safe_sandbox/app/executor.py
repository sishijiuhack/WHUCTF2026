import os
import sys
import traceback
from analyzer import validate_module_import, SecurityConfig

class TaskExecutor:
    
    @staticmethod
    def execute(
        code: str,
        security_config: SecurityConfig
    ):
        if security_config.runner_env_deny:
            os.environ.clear()
            
        TaskExecutor._sanitize_sys_modules(security_config)

        try:
            compiled_code = compile(code, "strictly santinized code", "exec")

            globals = {
                "__builtins__": TaskExecutor._filter_builtins(security_config)
            }

            exec(compiled_code, globals)

        except Exception:
            traceback.print_exc()
            
    @staticmethod
    def _filter_builtins(security_config: SecurityConfig):
        
        if len(security_config.builtins_deny) == 0:
            filtered = dict(__builtins__)
        else:
            filtered = {
                k: v
                for k, v in __builtins__.items()
                if k not in security_config.builtins_deny
            }

        filtered["__import__"] = TaskExecutor._create_safe_import(security_config)

        return filtered

    @staticmethod
    def _sanitize_sys_modules(security_config: SecurityConfig):
        safe_modules = {
            "builtins",
            "__main__",
            "sys",
            "traceback",
            "linecache",
            "importlib",
            "importlib.machinery",
        }

        if "*" in security_config.stdlib_allow:
            safe_modules.update(sys.stdlib_module_names)
        else:
            safe_modules.update(security_config.stdlib_allow)

        if "*" in security_config.external_allow:
            safe_modules.update(
                name
                for name in sys.modules.keys()
                if name not in sys.stdlib_module_names
            )
        else:
            safe_modules.update(security_config.external_allow)

        # keep modules marked as safe and submodules of those
        safe_prefixes = [safe + "." for safe in safe_modules]
        modules_to_remove = [
            name
            for name in sys.modules.keys()
            if name not in safe_modules
            and not any(name.startswith(prefix) for prefix in safe_prefixes)
        ]

        for module_name in modules_to_remove:
            del sys.modules[module_name]

    @staticmethod
    def _create_safe_import(security_config: SecurityConfig):
        original_import = __builtins__["__import__"]

        def safe_import(name, *args, **kwargs):
            is_allowed, error_msg = validate_module_import(name, security_config)

            if not is_allowed:
                assert error_msg is not None
                print(error_msg)
                raise Exception("Security violation detected")

            return original_import(name, *args, **kwargs)

        return safe_import