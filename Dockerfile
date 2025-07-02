FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY gunicorn_conf.py .

EXPOSE 8000

CMD ["gunicorn", "-c", "gunicorn_conf.py"]
