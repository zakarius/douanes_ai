FROM python:3.10

#RUN apt-get update -qq
#RUN apt-get install python3.10 python3-pip -y --no-install-recommends && rm -rf /var/lib/apt/lists_/*

WORKDIR /chroma
COPY ./ /chroma

RUN pip install --no-cache-dir --upgrade -r requirements.txt


EXPOSE 8000
#CMD uvicorn main:app --reload --workers 1 --host 0.0.0.0 --port 8000 --log-config log_config.yml