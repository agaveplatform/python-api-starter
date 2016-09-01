# Image: agaveapi/flask_api
# Base image for Agev APIs based on flask/Flask-restful.
# Usage: decend from this image, add your requirements file and service source code. The requirements file should
#        include agaveflask, specifying a particular version if necessary.

from python:alpine
RUN apk add --update git
RUN apk add --update bash && rm -f /var/cache/apk/*
RUN apk add --update --virtual=.build-dependencies alpine-sdk ca-certificates musl-dev gcc python-dev make cmake g++

RUN mkdir /_flask_api
ADD requirements.txt /_flask_api/requirements.txt
RUN pip install -r /_flask_api/requirements.txt

ADD entry.sh /_flask_api/entry.sh
RUN chmod +x /_flask_api/entry.sh

EXPOSE 5000

# provide sensible defaults for the configurations
ENV server dev
ENV package /service
ENV module api
ENV app app
ENV port 5000

CMD ["./_flask_api/entry.sh"]
