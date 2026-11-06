
from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)

# Demo credentials
USERS = {
    "admin": "admin123",
    "user1": "user123"
}

# Application-level security counters
login_metrics = {
    "total_attempts": 0,
    "successful_logins": 0,
    "failed_logins": 0
}

metrics_lock = Lock()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "auth-service",
        "status": "healthy"
    }), 200


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")

    with metrics_lock:
        login_metrics["total_attempts"] += 1

    if not username or not password:
        with metrics_lock:
            login_metrics["failed_logins"] += 1

        return jsonify({
            "message": "Username and password are required"
        }), 400

    if USERS.get(username) == password:
        with metrics_lock:
            login_metrics["successful_logins"] += 1

        return jsonify({
            "message": "Login successful",
            "authenticated": True,
            "username": username
        }), 200

    with metrics_lock:
        login_metrics["failed_logins"] += 1

    return jsonify({
        "message": "Invalid username or password",
        "authenticated": False
    }), 401


@app.route("/metrics", methods=["GET"])
def metrics():
    with metrics_lock:
        return jsonify({
            "service": "auth-service",
            "login_metrics": login_metrics.copy()
        }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)

