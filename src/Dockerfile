FROM python:3.8-alpine3.12

# install rust for orjson

RUN apk add build-base wget
ENV PATH="/root/.cargo/bin:${PATH}"
ENV RUSTFLAGS="-C target-feature=-crt-static"
RUN wget https://sh.rustup.rs -O rustup-init \
    && sh rustup-init -y --default-toolchain nightly-2020-09-14

# set work directory
WORKDIR /usr/src/app


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev \
    && apk add tzdata


# install dependencies
RUN pip3 install --upgrade pip
RUN pip install --no-binary=orjson orjson==3.3.1

COPY requirements.txt .
RUN pip3 --no-cache-dir install -r requirements.txt

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup -S app -g 1000 && adduser -u 1000 -S app -G app

# create the appropriate directories
ENV HOME=/home/app
WORKDIR $HOME

# copy project
COPY . $HOME


# chown all the files to the app user
# RUN chown -R app:app $HOME

# change to the app user
# USER app

RUN ls -la
# # run entrypoint.sh
ENTRYPOINT ["/home/app/entrypoint.sh"]
