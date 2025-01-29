# This is the test docker setup

FROM python:3.11-slim
WORKDIR /app
COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8900
CMD ["python", "./tests/test_api.py"]
