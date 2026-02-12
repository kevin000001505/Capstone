# Dockerfile
FROM prefecthq/prefect:3-latest

COPY docker/flows_package/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /opt/prefect-app

COPY prefect/ .