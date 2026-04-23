FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "-m", "flask", "--app", "app", "run", "--host=0.0.0.0", "--port=8080"]