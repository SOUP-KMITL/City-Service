# FROM python:3.6.4-alpine3.7
FROM python:3.6.4
ADD requirements.txt /tmp/requirements.txt
# RUN apk --update add build-base libffi-dev openssl-dev
RUN pip install pynacl && pip install -r /tmp/requirements.txt
ADD . /app
WORKDIR /app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--reload", "index:app"]
