
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Authentication service address
AUTH_SERVICE_URL = os.getenv(
    "AUTH_SERVICE_URL",
    "http://localhost:5001"
)

# Demo account balance
balance = 1000


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "payment-service",
        "status": "healthy"
    }), 200


@app.route("/balance", methods=["GET"])
def get_balance():
    return jsonify({
        "balance": balance
    }), 200


@app.route("/pay", methods=["POST"])
def make_payment():
    global balance

    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")
    amount = data.get("amount")

    if not username or not password or amount is None:
        return jsonify({
            "message": "Username, password and amount are required"
        }), 400

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({
            "message": "Invalid payment amount"
        }), 400

    if amount <= 0:
        return jsonify({
            "message": "Amount must be greater than zero"
        }), 400

    # Contact auth-service to verify the user
    try:
        auth_response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={
                "username": username,
                "password": password
            },
            timeout=5
        )
    except requests.RequestException:
        return jsonify({
            "message": "Authentication service unavailable"
        }), 503

    if auth_response.status_code != 200:
        return jsonify({
            "message": "Payment rejected: authentication failed"
        }), 401

    if amount > balance:
        return jsonify({
            "message": "Insufficient balance",
            "balance": balance
        }), 400

    balance -= amount

    return jsonify({
        "message": "Payment successful",
        "amount_paid": amount,
        "remaining_balance": balance
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
