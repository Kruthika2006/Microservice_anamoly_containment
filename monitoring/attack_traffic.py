import requests
import time

AUTH_URL = "http://localhost:5001"

print("Starting controlled failed-login test...")

attempts = 0

while True:
    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            json={
                "username": "admin",
                "password": "wrong_password"
            },
            timeout=3
        )

        attempts += 1

        if attempts % 10 == 0:
            print(
                f"Attempts: {attempts} | "
                f"Latest response: {response.status_code}"
            )

    except requests.RequestException as error:
        print("Request error:", error)

    time.sleep(0.5)
