# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy Python app code
COPY app.py /app/
COPY models/ /app/models/

# Install Python dependencies (assuming you have a requirements.txt)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Command to run your application
CMD ["python", "app.py"]