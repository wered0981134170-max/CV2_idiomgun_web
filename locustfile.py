from locust import HttpUser, task, between
import random

class Student(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_all_questions(self):
        self.client.get("/get_all_questions")

    @task(2)
    def leaderboard_get(self):
        self.client.get("/leaderboard")

    @task(1)
    def leaderboard_post(self):
        self.client.post("/leaderboard", json={
            "name": f"測試玩家{random.randint(1, 99)}",
            "score": random.randint(0, 100),
            "total": 100,
            "duration": random.randint(60, 300),
        })
