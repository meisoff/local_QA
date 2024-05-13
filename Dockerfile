FROM python:3.10

LABEL maintainer = "kalyrginwot@mail.ru"

ENV PYTHONBUFFERED 1

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "src/ui_bot/app.py"]
