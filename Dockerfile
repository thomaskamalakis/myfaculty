FROM python:3
RUN apt-get update && apt-get install -y build-essential python3-dev \
    libldap2-dev libsasl2-dev slapd ldap-utils tox gettext \
    lcov valgrind    
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
