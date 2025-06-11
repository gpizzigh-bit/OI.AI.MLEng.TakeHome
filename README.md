# Marine Classifier API

This repository contains the **Marine Classifier API**, a FastAPI-based service for image classification using a Triton Inference Server. The service is containerized and includes observability tools such as Prometheus, Grafana, Jager, and Fluent-bit.

✅ **Challenge Deliverables Fulfilled:**

* Create a RESTful API service with at least one endpoint that accepts an image path/url and returns the
classification result.
* Containerize the application using Docker.
* Provided observability features and monitoring dashboards.
* Enabled asynchronous request handling to process multiple requests in parallel.
* Use pre-commit hooks and lint the code.
* Add automated tests to ensure the service’s reliability. (for now coverage is bellow 30%, just to demonstrate the approach).

 **Extra Features:**
 * Implemented a dynamic loading mechanism based on CPU usage to switch between models.
 * Create a basic automatic Github CI pipeline to run the tests and check code quality.
 * Added a logging pipeline to capture and store logs in a structured format.
 * Use poetry for dependency management.
 * Implemented a NVIDIA Triton Inference Server for faster model inference.


⚠️ **Partial Kubernetes Deployment:**
Due to time constraints, the Kubernetes deployment is partially implemented and untested. However, the project structure (`k8s` directory) and deployment manifests are prepared for future deployment.

---

## Prerequisites

Make sure you have the following tools installed on your machine:

* [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  ⚠️ On Windows, WSL2 is required for Docker Desktop to work properly.
* [Powershell 7.5.1 or later](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.5)
  ⚠️ Required to run bash scripts on Windows.
---

## Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/gpizzigh-bit/OI.AI.MLEng.TakeHome.git
cd OI.AI.MLEng.TakeHome
```

---

### 2️⃣ Build and Open the Development Environment

You have two options:

#### Option 1 – **Manual Setup** (More Control)

1. Open the project in **VS Code**.

2. Ensure you have the **Dev Containers** extension installed and open the project in a container:

   * Open the command palette (`Ctrl+Shift+P`).
   * Select:

     ```
     Dev Containers: Open Folder in Container
     ```
   * Choose this project folder to launch the **preconfigured development environment**.

3. Once inside the container, navigate to the project root:

   ```bash
   cd /workspaces/OI.AI.MLEng.TakeHome
   ```

4. **Prepare the environment**:
   Make sure the Python environment is set up using Poetry:

   ```bash
   poetry install
   ```

5. **Download the test images**:

   ```bash
   bash scripts/get_test_images.sh
   ```

6. **Download and prepare the Triton models**:

   ```bash
   bash scripts/prepare_triton_models.sh
   ```

7. **Start the infrastructure** (using Docker Compose):

   ```bash
   bash scripts/setup-infra.sh
   ```

   This will start all required services, including:

   * `marine_classifier` API
   * Supporting services (e.g., databases, observability tools)

8. **Add your dev container to the `skynet` network**:

   ```bash
   sudo docker network connect skynet {your_container_name}
   ```
   Replace `{your_container_name}` with the name of your dev container.
    You can find the container name by running:

    ```bash
    docker ps
    ```

9. **Check if the API is ready**:
   Test the readiness endpoint manually to confirm it’s healthy:

   ```bash
   curl http://marine_classifier:29000/readiness
   ```

   If you see:

   ```json
   {"status":"ready"}
   ```

   it’s good to go!

10. **Run the API test scripts manually**:

* **ResNet50 predict API**:

  ```bash
  bash scripts/test_resnet50_api.sh
  ```
* **CPU load balancing smart API**:

  ```bash
  bash scripts/test_cpu_load_balancing.sh
  ```
* **Triton inference service API**:

  ```bash
  bash scripts/test_triton_api.sh
  ```
* **Load testing with Locust**:

  ```bash
  bash scripts/test_locust.sh
  ```

  Then open [http://localhost:8089](http://localhost:8089) in your browser to configure and run load tests.

11. For observability and monitoring, you can access the following tools:

| Tool           | URL                                              | Notes                                                                                                             |
| -------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| **API**        | [http://localhost:29000](http://localhost:29000) | API documentation available via ReDoc.                                                                            |
| **Prometheus** | [http://localhost:9090](http://localhost:9090)   | Monitoring and metrics (optional).                                                                                |
| **Grafana**    | [http://localhost:3000](http://localhost:3000)   | Default credentials: `USER: ocean_infinty` / `PASS: admin`.<br/>Preconfigured dashboard: “Marine Classifier API”. |
| **Jaeger**     | [http://localhost:16686](http://localhost:16686) | Distributed tracing.                                                                                              |

12. **When you’re done**, **stop and clean up resources**:

```bash
bash scripts/stop_and_clean.sh
```

#### Option 2 – **Automated Setup** (Recommended for Windows using WSL2)

1. Ensure WSL2 is installed and Docker Desktop is running.
2. Run the automated script to build a temporary container (`maestro`) and deploy the services using Docker Compose:

   ```bash
   ./scripts/run.sh
   ```

✅ What it does:

Prepares the environment inside the maestro container.

Deploys all Docker Compose services (marine_classifier, supporting tools).

Allows you to test various APIs and run load testing scenarios via Locust.

When finished, you can optionally clean up resources to ensure no leftover containers, volumes, or networks.

### 3️⃣ Access the Services

| Tool           | URL                                              | Notes                                                                                                             |
| -------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| **API**        | [http://localhost:29000](http://localhost:29000) | API documentation available via ReDoc.                                                                            |
| **Prometheus** | [http://localhost:9090](http://localhost:9090)   | Monitoring and metrics (optional).                                                                                |
| **Grafana**    | [http://localhost:3000](http://localhost:3000)   | Default credentials: `USER: ocean_infinty` / `PASS: admin`.<br/>Preconfigured dashboard: “Marine Classifier API”. |
| **Jaeger**     | [http://localhost:16686](http://localhost:16686) | Distributed tracing.                                                                                              |


Attention: For now the Kubernetes deployment is not wet implemented in the automated script, but you can find the manifests in the `k8s` directory for reference.

---

## Troubleshooting

* Ensure Docker Desktop is running and has sufficient resources (CPU, memory).
* If running on Windows, verify that WSL2 is properly configured.
* If issues persist, restart Docker Desktop and re-run the script.
* To be able to run bash scripts in Windows, you may need to install the new powershell >7.5.1.

---

## Kubernetes Deployment (Partial)

Although full Kubernetes deployment is not required for this challenge, the repository includes deployment manifests in the `k8s` directory for future use.
⚠️ Note: These configurations are not fully tested due to time constraints but should require only minor adjustments for a complete deployment.

---

## License

This project is intended for the Ocean Infinity Machine Learning Engineering challenge. All rights reserved.

---

Let me know if you’d like me to add a **"How to Contribute"** section, a **"License"** notice, or anything else! 🚀
