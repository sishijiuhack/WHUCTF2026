from dialect_runtime import DialectSpec, SessionRunner


def new_runner() -> SessionRunner:
    return SessionRunner(DialectSpec(name="上海话", key="shanghai"))
