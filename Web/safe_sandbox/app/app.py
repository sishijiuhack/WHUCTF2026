import io
import contextlib
from flask import Flask, request, jsonify, render_template
from analyzer import SecurityConfig, TaskAnalyzer
from executor import TaskExecutor

app = Flask(__name__)

app.secret_key = "you can try to access this one just for fun"

security_config = SecurityConfig(
    stdlib_allow={},
    external_allow=set(),
    builtins_deny={
        "eval", "exec", "compile", "open", "input", "breakpoint",
        "getattr", "object", "type", "vars", "setattr", "delattr",
        "hasattr", "dir", "memoryview", "__build_class__",
        "globals", "locals", "license", "help", "credits", "copyright"
    },
    runner_env_deny=True
)

analyzer = TaskAnalyzer(security_config)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/execute", methods=["POST"])
def execute():
    data = request.get_json()
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "No code provided"}), 400

    # Static analysis
    try:
        analyzer.validate(code)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Execute via TaskExecutor, capturing stdout/stderr
    stdout = io.StringIO()
    stderr = io.StringIO()

    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        TaskExecutor.execute(code, security_config)

    return jsonify({
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
