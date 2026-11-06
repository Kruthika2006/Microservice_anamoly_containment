import csv
import os

FILES = {
    "normal_telemetry_v2.csv": 0,
    "attack_telemetry_v2.csv": 1
}

output = []

for filename, label in FILES.items():

    with open(filename, newline="") as file:
        rows = list(csv.DictReader(file))

    previous = {}

    for row in rows:
        container = row["container"]

        current = {
            "timestamp": row["timestamp"],
            "container": container,
            "label": label,
            "cpu_percent": float(row["cpu_percent"]),
            "memory_percent": float(row["memory_percent"]),
            "process_count": int(row["process_count"]),
            "network_rx_delta": 0,
            "network_tx_delta": 0,
            "new_login_attempts": 0,
            "new_successful_logins": 0,
            "new_failed_logins": 0
        }

        rx = int(row["network_rx_bytes"])
        tx = int(row["network_tx_bytes"])

        if container in previous:
            current["network_rx_delta"] = max(
                0, rx - previous[container]["rx"]
            )
            current["network_tx_delta"] = max(
                0, tx - previous[container]["tx"]
            )

        if container == "auth-service":
            attempts = int(row["total_login_attempts"])
            successes = int(row["successful_logins"])
            failures = int(row["failed_logins"])

            if container in previous and "attempts" in previous[container]:
                current["new_login_attempts"] = max(
                    0, attempts - previous[container]["attempts"]
                )
                current["new_successful_logins"] = max(
                    0, successes - previous[container]["successes"]
                )
                current["new_failed_logins"] = max(
                    0, failures - previous[container]["failures"]
                )

            previous[container] = {
                "rx": rx,
                "tx": tx,
                "attempts": attempts,
                "successes": successes,
                "failures": failures
            }
        else:
            previous[container] = {"rx": rx, "tx": tx}

        output.append(current)

output_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "prepared_telemetry.csv"
)

with open(output_file, "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=output[0].keys())
    writer.writeheader()
    writer.writerows(output)

print("Prepared dataset created successfully!")
print("Total records:", len(output))
print("Normal records:", sum(r["label"] == 0 for r in output))
print("Attack records:", sum(r["label"] == 1 for r in output))
print("Output:", output_file)
