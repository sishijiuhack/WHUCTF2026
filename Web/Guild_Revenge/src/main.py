from flask import Flask, jsonify, render_template, request
import os
import time

app = Flask(__name__)


def is_input_valid(value: str) -> bool:
    """
    Placeholder validation logic.
    Replace this function with your own verification rules later.
    """
    flag = os.getenv("GZCTF_FLAG")
    if flag is None:
        flag = "flag{test_flag_please_contact_admin}"
    if flag<value:
        time.sleep(3)
    return flag == value


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/validate", methods=["POST"])
def validate():
    data = request.get_json(silent=True) or {}
    user_inputs = data.get("content", [])

    if not isinstance(user_inputs, list):
        return jsonify(
            {
                "valid": False,
                "message": "请输入数组格式的数据",
                "results": [],
            }
        ), 400

    results = []
    for item in user_inputs:
        value = str(item)
        valid = is_input_valid(value)
        results.append(
            {
                "value": item,
                "valid": valid,
                "message": "输入正确" if valid else "输入不正确",
            }
        )

    all_valid = all(result["valid"] for result in results) if results else False

    return jsonify(
        {
            "valid": all_valid,
            "message": "全部输入正确" if all_valid else "存在不正确的输入",
            "results": results,
        }
    )


if __name__ == "__main__":
    app.run(debug=False, port=8080, host="0.0.0.0")
