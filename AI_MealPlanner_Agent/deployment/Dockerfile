FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p memory logs outputs data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV GEMINI_API_KEY=${GEMINI_API_KEY}

# Run the application
CMD ["uvicorn", "main_agent:app", "--host", "0.0.0.0", "--port", "8000"]