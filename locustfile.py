from locust import HttpUser, between, task


class BooksUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self):
        response = self.client.post(
            "/auth/token",
            json={"username": "admin", "password": "admin"},
            name="/auth/token",
        )
        response.raise_for_status()
        access_token = response.json()["access_token"]
        self._headers = {"Authorization": f"Bearer {access_token}"}

    @task
    def get_books(self):
        with self.client.get(
            "/books/?limit=10",
            headers=self._headers,
            name="/books/",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
