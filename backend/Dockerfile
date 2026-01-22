# 1. Use a lightweight Python base (saves space)
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy dependencies first (Optimization: caches this layer)
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the actual code
COPY . .

# 6. Expose the port FastAPI runs on
EXPOSE 8000

# 7. Command to start the server
# Note: We bind to 0.0.0.0 so the outside world can reach it
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]