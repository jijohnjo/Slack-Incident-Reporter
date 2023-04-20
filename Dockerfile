FROM python:3.11.2-alpine3.17

WORKDIR /opt/app

ARG SLACK_TOKEN
ENV SLACK_BOT_TOKEN $SLACK_TOKEN

COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

EXPOSE 5001

CMD ["python", "main.py"]