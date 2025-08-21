# Use Python 3.12 Alpine for minimal size
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Copy requirements file first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY .env .
COPY templates/ ./templates/

# Expose port 5005
EXPOSE 5005

# Run the application
CMD ["python", "app.py"]
