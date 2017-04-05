FROM debian

ADD https://www.postgresql.org/media/keys/ACCC4CF8.asc /tmp/ACCC4CF8.asc
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    echo "Acquire::http {No-Cache=True;};" > /etc/apt/apt.conf.d/no-cache && \
    apt-key add /tmp/ACCC4CF8.asc
RUN apt-get update && \
    apt-get install -y \
# Development files
      apt-utils build-essential git mercurial software-properties-common \
# Python libraries
      python python-dev python-setuptools \
# uWSGI for hosting applications
      uwsgi uwsgi-plugin-python \
# Supervisor to manage the uwsgi instance
      supervisor \
# Nginx for wsgi socket handling
      nginx \
# Libraries
      libpq-dev fontconfig libfontconfig1 libfreetype6 libjpeg62-turbo \
      libxml2-dev libxslt1-dev \
      libxrender1 libffi-dev postgresql-server-dev-9.5 \
# Fonts
      xfonts-base xfonts-75dpi \
# Useful tools
      postgresql-client-9.5 gnupg curl && \
    apt-get clean && \
    rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

RUN easy_install -U pip

# wkhtmltopdf-static, since we need the static version
COPY ./wkhtmltox-0.12.2.4_linux-jessie-amd64.deb /tmp/wkhtmltox.deb
RUN dpkg -i /tmp/wkhtmltox.deb

# Just install these now, since they are long builds
RUN pip install \
	  requests \
      bcrypt \
      cffi \
      cryptography \
      ndg-httpsclient \
      newrelic \
      pyasn1 \
      pyopenssl \
      six \
      sqlalchemy \
      urllib3

COPY ./src opt/rsplib/

WORKDIR opt/rsplib/