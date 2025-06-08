import os
import random

from locust import HttpUser, between

# List of endpoints to test
API_ENDPOINTS = [
    # "/api/v1/predict",
    # "/api/v1/smart_predict",
    "/api/v1/triton_predict",
]


class ImageClassificationUser(HttpUser):
    host = "http://localhost:9000"
    wait_time = between(1, 3)

    def get_random_image(self):
        image_dir = "images"
        image_files = [
            f
            for f in os.listdir(image_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        if not image_files:
            print("No images found in the directory.")
            return None, None
        image_file = random.choice(image_files)
        image_path = os.path.join(image_dir, image_file)
        return image_file, image_path

    def send_request(self, endpoint):
        image_file, image_path = self.get_random_image()
        if not image_file:
            return

        with open(image_path, "rb") as img:
            files = {"file": (image_file, img, "image/jpeg")}
            with self.client.post(
                endpoint, files=files, catch_response=True
            ) as response:
                if response.status_code == 200:
                    try:
                        data = response.json()
                        predictions = data.get("result") or data.get("predictions")
                        print(f"[{endpoint}] {image_file}: {predictions}")
                        response.success()
                    except Exception as e:
                        response.failure(f"Failed to parse JSON: {e}")
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")


# Dynamically create tasks list
def make_task(endpoint):
    def task_fn(user_instance):
        user_instance.send_request(endpoint)

    return task_fn


# Create a list of tasks for only the enabled endpoints
ImageClassificationUser.tasks = [make_task(endpoint) for endpoint in API_ENDPOINTS]
