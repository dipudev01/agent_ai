"""Load test using Locust. Run: locust -f tests/load/locustfile.py --host http://localhost:8000"""

from locust import HttpUser, between, task


class ChatUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": "customer@demo.com", "password": "demo1234"},
        )
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def chat_loan(self):
        self.client.post(
            "/api/v1/chats",
            json={"message": "Can I get a ₹10 lakh personal loan?"},
            headers=self.headers,
        )

    @task(2)
    def chat_support(self):
        self.client.post(
            "/api/v1/chats",
            json={"message": "How do I reset my netbanking password?"},
            headers=self.headers,
        )

    @task(1)
    def agent_catalog(self):
        self.client.get("/api/v1/agents", headers=self.headers)