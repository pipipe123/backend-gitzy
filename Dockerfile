FROM python:3.14-slim

WORKDIR /app

COPY requeriments.text .
RUN pip install --no-cache-dir -r requeriments.text

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
