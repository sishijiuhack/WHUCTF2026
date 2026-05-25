from dialect_runtime import DialectSpec, SessionRunner


def new_runner() -> SessionRunner:
    return SessionRunner(DialectSpec(name="东北话", key="dongbei"))
