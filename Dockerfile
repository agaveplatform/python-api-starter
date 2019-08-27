# Image: agaveplatform/python-api-starter
# Base image for Agave Platform APIs based on flask/Flask-RESTful.
# Usage: Build from this image, add your requirements file and service source code. The requirements file should
#        include git+https://github.com/agaveplatform/python-api-starter.git#egg=agaveflask,
#				 specifying a particular branch/version if necessary.

FROM ubuntu:18.04
RUN apt-get update && \
		apt-get install -y python-dev \
											 libxml2-dev \
											 libxslt1-dev \
											 python3-pip \
											 git \
											 ca-certificates && \
		mkdir /_flask_api

ADD requirements.txt /_flask_api/requirements.txt

RUN pip3 install -r /_flask_api/requirements.txt

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
