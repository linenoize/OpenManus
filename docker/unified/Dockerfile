FROM python:3.9

RUN apt-get update && apt-get -y install tree

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY . .

# Make sure .env file exists (will be overridden by mounted volume if provided)
RUN touch .env

CMD ["sh", "/app/docker/unified/start.sh"]