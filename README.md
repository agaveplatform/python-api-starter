# agaveflask #

## Overview ##

A common set of Python modules for writing flask services for the Agave Platform. The package officially requires Python
3.4+, though some functionality may work with Python 2.


## Installation ##
pip install agaveflask

Requires Python header files and a C++ compiler on top of gcc. On Debian/Ubuntu systems:
apt-get install python3-dev g++


## Usage ##

agaveflask provides the following modules:

* auth.py - configurable authentication/authorization routines.
* config.py - config parsing.
* errors.py - exception classes raised by agaveflask.
* store.py - python bindings for persistence.
* utils.py - general request/response utilities.

It relies on a configuration file for the service. Create a file called service.conf in one of `/`, `/etc`, or `$pwd`.
See service.conf.ex in this repository for settings used by this library.


## Using Docker ##

### Packaging ###
If you are packaging your flask service with Docker, agaveflask provides a base image, agaveapi/flask_api, that
simplifies your Dockerfile and provides a configurable entrypoint for both development and production deployments. In
most cases, all you need to do is add your service code and your requirements.txt file. For example, if you have a
flask service with a requirements.txt file and code that resides in a directory called "service", the Dockerfile can
be as simple as:

```
from agaveapi/flask_api
ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
ADD service /service
```

### Suggested Package Layout ###

For simple microservices, we make the following recommendations for minimal configuration at deployment time.

* Place the service code in a Python package called `services` that resides at the root of the DOcker image (i.e. `/service`).
* Within `/service`, have a python module called `api.py` where the wsgi application is instantiated.
* Call the actual wsgi application object `app`.

Beyond standard flask operations, additional suggestions for the `api.py` module include:

* Add cors support.
* Set up authentication and authorization for your API using the agaveflask authn_and_authz() method.
* Start a development server within `__main__`.

We also recommend

Here is a typical example:

```
from flask import Flask
from flask_cors import CORS

from agaveflask.utils import AgaveApi
from agaveflask.auth import authn_and_authz

from resources import JwtResource

# create the wsgi application object
app = Flask(__name__)

# add CORS support
CORS(app)

# create an AgaveApi object so that convenience utilities are available:
api = AgaveApi(app)

# Set up Authn/z for the API
@app.before_request
def auth():
    authn_and_authz()

# Add the resources
api.add_resource(JwtResource, '/admin/jwt')

# start a development server
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
```

### Deployment Configuration ###
The entry point is configured through environmental variables. Using the `server` variable toggles between a
development server you have created in your api module and gunicorn, meant for production.
All other settings are used to help the entrypoint find
your wsgi application. If you are able to use the recommended file system structure and layout, you may be able to
rely exclusively on the image defaults.

Here is a complete list of config variables, their usage, and their default values:

* server: Value "dev" attempts to starts up a development server by executing your module's `__main__` method. Any
other value starts up gunicorn. Default is 'dev'.
* package: path to package containing service code (no trailing slash). Default is '/service'.
* module: name of python module (not including '.py') containing the wsgi application object. Default is 'api'.
* app: name of the wsgi application object. Default is 'app'.
* port: port to start the server on when running with gunicorn. Default is 5000.


### Docker compose Examples ###
The following snippet from a hypothetical docker-compose.yml file illustrates typical usage. In this example we have a
folder, `services`, containing two services that we are bundling into the same docker image (`jdoe/my_services`).
Because of this we need to set the indvidual packages for each using environmental variables. We also set the server
variable so that we use gunicorn.

```
.  .  .

serviceA:
    image: jdoe/my_services
    ports:
        - "5000:5000"
    volumes:
        - ./local-dev.conf:/etc/service.conf
    environment:
        package: /services/serviceA
        server: gunicorn

serviceB:
    image: jdoe/my_services
    ports:
        - "5001:5000"
    volumes:
        - ./local-dev.conf:/etc/service.conf
    environment:
        package: /services/serviceA
        server: gunicorn

.  .  .

```
