#!/bin/bash
#
# Entrypoint to flask powered Agave API. Configure the entrypoint using the following environmental variables:
# server: "dev" starts up a development server. Any other value starts up gunicorn.
# package: path to package containing service code.
# module: name of python module (not including '.py') containing the wsgi application object.
# app: name of the wsgi application object.
# port: port to start the server on when running with gunicorn.


if [ $server = "dev" ]; then
    python3 -u "$package/$module".py
else
    cd $package
    /usr/local/bin/gunicorn -w 2 -b :$port $module:$app
fi
