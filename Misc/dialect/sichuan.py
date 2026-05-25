from dialect_runtime import DialectSpec, SessionRunner


def new_runner() -> SessionRunner:
    return SessionRunner(DialectSpec(name="四川话", key="sichuan"))
