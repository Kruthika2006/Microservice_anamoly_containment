import time
import docker
import requests
import joblib
import pandas as pd
from datetime import datetime

client = docker.from_env()

# Load trained model
package = joblib.load("auth_anomaly_model_v2.pkl")
model = package["model"]
features = package["features"]

AUTH_METRICS_URL = "http://localhost:5001/metrics"

previous = {}

def collect_login_metrics():
    try:
        response = requests.get(AUTH_METRICS_URL, timeout=3)
        response.raise_for_status()
        return response.json()["login_metrics"]
    except Exception as error:
        print("Login metrics error:", error)
        return None


def collect_container_metrics(name):
    container = client.containers.get(name)
    stats = container.stats(stream=False)

    cpu_stats = stats["cpu_stats"]
    previous_cpu = stats["precpu_stats"]

    cpu_delta = (
        cpu_stats["cpu_usage"]["total_usage"]
        - previous_cpu["cpu_usage"]["total_usage"]
    )

    system_delta = (
        cpu_stats["system_cpu_usage"]
        - previous_cpu["system_cpu_usage"]
    )

    online_cpus = cpu_stats.get(
        "online_cpus",
        len(cpu_stats["cpu_usage"].get("percpu_usage", []))
    )

    cpu_percent = 0.0

    if system_delta > 0 and cpu_delta >= 0:
        cpu_percent = (
            cpu_delta / system_delta
        ) * online_cpus * 100

    memory = stats["memory_stats"]
    memory_usage = memory.get("usage", 0)
    memory_limit = memory.get("limit", 0)

    memory_percent = (
        memory_usage / memory_limit * 100
        if memory_limit else 0
    )

    networks = stats.get("networks", {})

    rx = sum(n.get("rx_bytes", 0) for n in networks.values())
    tx = sum(n.get("tx_bytes", 0) for n in networks.values())

    process_count = len(container.top().get("Processes", []))

    return {
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory_percent, 2),
        "process_count": process_count,
        "network_rx_bytes": rx,
        "network_tx_bytes": tx
    }


def main():
    print("Starting live anomaly detection...")
    print("Monitoring auth-service. Press Ctrl+C to stop.")

    while True:
        try:
            name = "auth-service"

            metrics = collect_container_metrics(name)
            login = collect_login_metrics()

            if login is None:
                time.sleep(10)
                continue

            current = {
                **metrics,
                "total_login_attempts": login["total_attempts"],
                "successful_logins": login["successful_logins"],
                "failed_logins": login["failed_logins"]
            }

            if name not in previous:
                previous[name] = current
                print("Baseline captured. Waiting for next sample...")
                time.sleep(10)
                continue

            old = previous[name]

            def delta(key):
                value = current[key] - old[key]
                return max(0, value)

            telemetry = {
                "cpu_percent": current["cpu_percent"],
                "memory_percent": current["memory_percent"],
                "process_count": current["process_count"],
                "network_rx_delta": delta("network_rx_bytes"),
                "network_tx_delta": delta("network_tx_bytes"),
                "new_login_attempts": delta("total_login_attempts"),
                "new_successful_logins": delta("successful_logins"),
                "new_failed_logins": delta("failed_logins")
            }

            previous[name] = current

            data = pd.DataFrame([telemetry], columns=features)

            score = float(model.decision_function(data)[0])
            prediction = int(model.predict(data)[0])

            status = "ATTACK" if prediction == -1 else "NORMAL"

            # Risk classification
            if score >= 0:
                risk = "LOW"
            elif score >= -0.02:
                risk = "MEDIUM"
            else:
                risk = "HIGH"

            # Dependency-aware containment simulation
            blast_radius_cost = 100
            breach_cost = 60

            if risk == "LOW":
                action = "LOG"
            elif risk == "MEDIUM":
                action = "RATE_LIMIT"
            elif blast_radius_cost <= breach_cost:
                action = "ISOLATE"
            else:
                action = "ALERT"

            print("\nTime:", datetime.now().isoformat())
            print("Features:", telemetry)
            print("Anomaly score:", round(score, 5))
            print("Detection:", status)
            print("Risk level:", risk)
            print("Recommended action:", action)
            print("Mode: SIMULATION ONLY")
        except KeyboardInterrupt:
            print("\nLive detection stopped.")
            break

        except Exception as error:
            print("Detection error:", error)

        time.sleep(10)


if __name__ == "__main__":
    main()
