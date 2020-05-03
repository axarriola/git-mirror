FROM python:3.8-slim

EXPOSE 2555
WORKDIR /server

COPY ./requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

COPY ./.env .
COPY ./main.py .
COPY ./constants.py .

RUN groupadd -r -g 1124 gitmirror && \
    useradd -g 1124 -u 1124 gitmirror && \
    chown -R gitmirror:gitmirror /server

USER gitmirror

CMD [ "uvicorn", "main:app", "--host=0.0.0.0", "--port=2555" ]
