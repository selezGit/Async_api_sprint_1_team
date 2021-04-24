FROM python:3.9

ARG REQUIREMENTS_FILE=requirements.txt
ARG dir=etl

COPY etl/requirements.txt /requirements.txt
RUN python -m pip install --upgrade pip
RUN python -m pip install -r /requirements.txt

WORKDIR /

COPY ${dir}/__init__.py /etl.py

ENTRYPOINT [ "python", "etl.py" ]