from locust import HttpUser, task, between

class DetectUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(5)
    def predict(self):
        payload = {
            "url": "ya.ru",
            "title": "Сегодня: +14⁠…⁠+20⁠° · переменная облачность, без осадков · слабый ветер 3⁠–⁠5 м⁠/⁠с, порывы до 17 м⁠/⁠с"
        }
        self.client.post("/v1/predict", json=payload)

    @task(1)
    def health(self):
        self.client.get("/health")