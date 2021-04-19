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

# create the appropriate directories
ENV HOME=/home/app
WORKDIR $HOME

# copy project
COPY . $HOME

RUN chmod +x /home/app/entrypoint.sh

# # run entrypoint.sh
ENTRYPOINT ["/home/app/entrypoint.sh"]
