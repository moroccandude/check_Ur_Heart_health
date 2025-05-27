FROM python:3.9

WORKDIR /app

# Install Java if needed
RUN apt-get update && apt-get install -y default-jre-headless && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application
COPY . .

EXPOSE 5000

# Use python -m to avoid PATH issues
CMD ["python", "-m", "mlflow", "models", "serve", "-m", "model", "-h", "0.0.0.0", "-p", "5000"]