# FROM python:3.6.4-alpine3.7
FROM python:3.6.4
ADD requirements.txt /tmp/requirements.txt
# RUN apk --update add build-base libffi-dev openssl-dev py-pynacl
RUN pip install -r /tmp/requirements.txt
ADD . /app
WORKDIR /app
# ENV FLASK_APP index.py
# ENV FLASK_DEBUG 1
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--reload", "index:app"]
# CMD ["flask", "run", "-h", "0.0.0.0", "-p", "5000"]
