FROM python:3.6.3-alpine3.6
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ADD . /app
WORKDIR /app
# ENV FLASK_APP index.py
# ENV FLASK_DEBUG 1
# CMD ["flask", "run", "-h", "0.0.0.0", "-p", "5000"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--reload", "index:app"]
