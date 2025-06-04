from locust import HttpUser, task, between
import os
import random

class ImageClassificationUser(HttpUser):
    host = "http://localhost:8000"  # Replace with your FastAPI host
    wait_time = between(1, 3)

    @task
    def classify_image(self):
        image_dir = "images"
        image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not image_files:
            print("No images found in the directory.")
            return

        image_file = random.choice(image_files)
        image_path = os.path.join(image_dir, image_file)

        with open(image_path, 'rb') as img:
            files = {'file': (image_file, img, 'image/jpeg')}
            response = self.client.post("/api/v1/predict", files=files)
            if response.status_code == 200:
                result = response.json().get("result", {})
                print(f"{image_file}: {result.get('class_name')} (Confidence: {result.get('confidence'):.2f})")
            else:
                print(f"Failed to classify {image_file}. Status code: {response.status_code}")

