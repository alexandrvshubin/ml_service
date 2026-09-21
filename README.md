
# Detect Service (ML PRO HW1)


1. **Тесты:**
   ```bash
   uv sync
   uv run pytest
2. **Compose:**
   ```bash
   docker compose up -d --build
   curl http://localhost:8000/health
   docker compose down
2. **Kind:**
   ```bash
   kind load docker-image detect-service:latest --name mlpro
   kubectl apply -f k8s/
   kubectl port-forward svc/detect-service 8080:80
   curl http://localhost:8080/health3.   