
import requests
import time
import random

AUTH_URL = "http://localhost:5001"
PAYMENT_URL = "http://localhost:5002"

print("Starting normal application traffic...")

while True:

    try:
        # Generate a login request
        login_response = requests.post(
            f"{AUTH_URL}/login",
            json={
                "username": "admin",
                "password": "admin123"
            },
            timeout=5
        )

        print("Login:", login_response.status_code)

        # Generate a payment request
        payment_response = requests.post(
            f"{PAYMENT_URL}/pay",
            json={
                "username": "admin",
                "password": "admin123",
                "amount": 1
            },
            timeout=5
        )

        print("Payment:", payment_response.status_code)

    except requests.RequestException as error:
        print("Request error:", error)

    # Wait a random interval before the next request
    time.sleep(random.uniform(2, 5))
