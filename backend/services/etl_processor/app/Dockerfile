FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL application code
COPY . .

# Make start script executable
RUN chmod +x start.sh

EXPOSE 5000

# Run both FastAPI + ETL worker
CMD ["./start.sh"]