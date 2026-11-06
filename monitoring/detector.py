import joblib
import pandas as pd

# Load trained model
package = joblib.load("auth_anomaly_model.pkl")

model = package["model"]
features = package["features"]

def detect_anomaly(telemetry):
    data = pd.DataFrame([telemetry], columns=features)

    score = model.decision_function(data)[0]
    prediction = model.predict(data)[0]

    risk_score = max(0, min(1, (0.15301532 - score) / (
        0.15301532 - (-0.18704461)
    )))

    if prediction == -1:
        status = "ATTACK"
    else:
        status = "NORMAL"

    return {
        "status": status,
        "anomaly_score": float(score),
        "risk_score": float(risk_score)
    }


if __name__ == "__main__":

    sample = {
    "cpu_percent": 0.03,
    "memory_percent": 0.32,
    "process_count": 1,
    "network_rx_delta": 0,
    "network_tx_delta": 0,
    "new_login_attempts": 8,
    "new_successful_logins": 8,
    "new_failed_logins": 0
}
    result = detect_anomaly(sample)

    print("Detection Result:")
    print(result)
