FROM python:3.6.7-alpine3.7

RUN mkdir -p /opt/pi-k8s

WORKDIR /opt/pi-k8s

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD lib lib
ADD test test

ADD setup.py .

ENV PYTHONPATH "/opt/pi-k8s/lib:${PYTHONPATH}"

CMD "/opt/pi-k8s/bin/daemon.py"
