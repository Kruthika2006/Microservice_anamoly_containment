
import docker
import time
import json
import csv
import os
import requests
from datetime import datetime

client = docker.from_env()

CONTAINERS = [
    "auth-service",
    "payment-service"
]

# Always save the CSV beside this script.
CSV_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "telemetry.csv"
)

AUTH_METRICS_URL = "http://localhost:5001/metrics"

FIELDS = [
    "timestamp",
    "container",
    "status",
    "cpu_percent",
    "memory_usage_bytes",
    "memory_percent",
    "network_rx_bytes",
    "network_tx_bytes",
    "process_count",
    "total_login_attempts",
    "successful_logins",
    "failed_logins"
]


def collect_login_metrics():
    """Read application-level login counters from auth-service."""

    try:
        response = requests.get(
            AUTH_METRICS_URL,
            timeout=3
        )
        response.raise_for_status()

        data = response.json()
        return data["login_metrics"]

    except (requests.RequestException, KeyError, ValueError) as error:
        print(f"Could not collect login metrics: {error}")
        return None


def collect_container_data(container_name):

    try:
        container = client.containers.get(container_name)
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
            ) * online_cpus * 100.0

        memory_usage = stats["memory_stats"].get("usage", 0)
        memory_limit = stats["memory_stats"].get("limit", 0)

        memory_percent = 0.0

        if memory_limit > 0:
            memory_percent = (
                memory_usage / memory_limit
            ) * 100.0

        networks = stats.get("networks", {})

        network_rx = sum(
            network.get("rx_bytes", 0)
            for network in networks.values()
        )

        network_tx = sum(
            network.get("tx_bytes", 0)
            for network in networks.values()
        )

        processes = container.top()
        process_count = len(processes.get("Processes", []))

        # Login counters belong only to auth-service.
        total_attempts = ""
        successful_logins = ""
        failed_logins = ""

        if container_name == "auth-service":
            login_data = collect_login_metrics()

            if login_data is not None:
                total_attempts = login_data.get("total_attempts", "")
                successful_logins = login_data.get("successful_logins", "")
                failed_logins = login_data.get("failed_logins", "")

        return {
            "timestamp": datetime.now().isoformat(),
            "container": container_name,
            "status": container.status,
            "cpu_percent": round(cpu_percent, 2),
            "memory_usage_bytes": memory_usage,
            "memory_percent": round(memory_percent, 2),
            "network_rx_bytes": network_rx,
            "network_tx_bytes": network_tx,
            "process_count": process_count,
            "total_login_attempts": total_attempts,
            "successful_logins": successful_logins,
            "failed_logins": failed_logins
        }

    except Exception as error:
        print(f"Error monitoring {container_name}: {error}")
        return None


def save_to_csv(record):

    file_exists = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS
        )

        if not file_exists or os.path.getsize(CSV_FILE) == 0:
            writer.writeheader()

        writer.writerow(record)


def monitor_containers():

    print("Starting telemetry collection...")
    print(f"Saving records to {CSV_FILE}")

    try:
        while True:

            for name in CONTAINERS:

                record = collect_container_data(name)

                if record:
                    print(json.dumps(record))
                    save_to_csv(record)

            time.sleep(10)

    except KeyboardInterrupt:
        print("\nTelemetry collection stopped.")


if __name__ == "__main__":
    monitor_containers()

