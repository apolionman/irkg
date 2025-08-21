from locust import HttpUser, task, between
import os

class VLLMUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def complete(self):
        self.client.post("/v1/completions", json={
            "model": "meta-llama/Llama-3.2-1B-Instruct",
            "prompt": "Stress test this prompt.",
            "max_tokens": 100
        }, headers={
            "Authorization": f"Bearer {os.getenv('VLLM_API_KEY')}",
            "Content-Type": "application/json"
        })
