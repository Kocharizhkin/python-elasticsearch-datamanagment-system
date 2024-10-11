# Dockerfile
FROM python:3.12

# Set working directory
WORKDIR /app

# Copy Python app code
COPY app.py /app/
COPY db/ /app/db/
COPY routes/ /app/routes/

# Install Python dependencies (assuming you have a requirements.txt)
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y build-essential libpq-dev gcc
RUN python3 -m pip install -r requirements.txt --no-cache-dir
RUN apt-get autoremove && apt-get clean

# Command to run your application
CMD ["python", "app.py"]