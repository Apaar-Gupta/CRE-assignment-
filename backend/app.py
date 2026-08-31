"""
RateLab - Flask backend.

Serves the frontend (templates + static files from ../frontend) and exposes
a single JSON API endpoint, /api/predict, used by the Order & k Solver tab.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import os
import sys

from flask import Flask, render_template, request, jsonify

# Make "models" and "utils" importable as top-level packages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.fitter import run_manual, run_auto  # noqa: E402
from utils.validators import ValidationError, require_arrays_same_length  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static"),
)


# ---------- Page routes ----------

@app.route("/")
def home():
    return render_template("index.html", active_tab="home")


@app.route("/order-predictor")
def order_predictor():
    return render_template("order_predictor.html", active_tab="order-predictor")


@app.route("/project2")
def project2():
    return render_template("project2.html", active_tab="project2")


@app.route("/project3")
def project3():
    return render_template("project3.html", active_tab="project3")


# ---------- API ----------

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "No JSON body received."}), 400

    mode = data.get("mode", "manual")  # "manual" or "auto"
    reaction_type = data.get("reaction_type")

    t = data.get("t")
    C_A = data.get("C_A")

    if not t or not C_A:
        return jsonify({"error": "Both 't' and 'C_A' data arrays are required."}), 400

    try:
        require_arrays_same_length(("t", t), ("C_A", C_A))
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    payload = {
        "t": t,
        "C_A": C_A,
        "C_B0": data.get("C_B0"),
        "C_P0": data.get("C_P0"),
        "C_B_data": data.get("C_B_data"),
        "C_Ae": data.get("C_Ae"),
    }

    try:
        if mode == "auto":
            result = run_auto(payload)
        else:
            if not reaction_type:
                return jsonify({"error": "reaction_type is required in manual mode."}), 400
            result = run_manual(reaction_type, payload)
        return jsonify({"mode": mode, "result": result})
    except (ValueError, ValidationError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Unexpected error: {exc}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
