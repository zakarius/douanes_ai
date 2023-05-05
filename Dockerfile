FROM python:3.10

#RUN apt-get update -qq
#RUN apt-get install python3.10 python3-pip -y --no-install-recommends && rm -rf /var/lib/apt/lists_/*

WORKDIR /chroma
COPY ./ /chroma
COPY ./docker_entrypoint.sh /docker_entrypoint.sh

RUN pip install --no-cache-dir --upgrade -r requirements.txt


EXPOSE 8000
CMD ["/docker_entrypoint.sh"]