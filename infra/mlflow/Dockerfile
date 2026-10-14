FROM python:3.13-slim
# psycopg: backend store Postgres; boto3: artifact store S3 (MinIO).
RUN pip install --no-cache-dir mlflow==3.16.1 "psycopg[binary]==3.2.12" boto3==1.40.61
