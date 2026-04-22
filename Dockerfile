FROM python:3.11

WORKDIR /app

COPY . .

RUN cat requirements.txt
RUN pip install -r requirements.txt

CMD ["python", "bot.py"]