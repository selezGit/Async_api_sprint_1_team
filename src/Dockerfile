FROM python:3.9.4-slim-buster


RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y netcat-openbsd gcc && \
    apt-get clean


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# set work directory
WORKDIR /usr/src/app


# install dependencies
RUN pip3 install --upgrade pip

COPY requirements.txt .
RUN pip3 --no-cache-dir install -r requirements.txt

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --no-create-home --group app
# RUN chown -R app:app /usr/src/app && chmod -R 755 /usr/src/app


# copy project
COPY . .

RUN chmod +x /usr/src/app/entrypoint.sh

# # run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

CMD uvicorn main:app --reload --workers 1 --host 0.0.0.0 --port 8000


#CMD gunicorn main:app --bind 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker
    