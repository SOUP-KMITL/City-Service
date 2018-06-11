FROM python:3.6.3-alpine3.6
ADD requirements.txt /tmp/requirements.txt
ADD repositories /etc/apk/repositories
RUN apk add --update gcc autoconf musl-dev
RUN pip install -r /tmp/requirements.txt
ADD . /app
WORKDIR /app
CMD ["gunicorn", "-w", "8", "-b", "0.0.0.0:5000", "route:app"]
# CMD ["python", "profiling_test.py"]
