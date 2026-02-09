# Dockerfile
FROM prefecthq/prefect:3-latest

WORKDIR /opt/flows

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flows/ flows/