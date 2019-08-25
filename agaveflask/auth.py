# Utilities for authn/z
import base64
import re

# from Crypto.Signature import PKCS1_v1_5
# from Crypto.PublicKey import RSA
#from Crypto.Hash import SHA256
from flask import g, request
import jwt
import requests

from .config import Config
from .errors import PermissionsError,BaseAgaveflaskError

from .logs import get_logger
logger = get_logger(__name__)

# jwt.verify_methods['SHA256WITHRSA'] = (
#     lambda msg, key, sig: PKCS1_v1_5.new(key).verify(SHA256.new(msg), sig))
# jwt.prepare_key_methods['SHA256WITHRSA'] = jwt.prepare_RS_key

def _get_pub_key_url():
    """Look for the jwt key in the config file, in a named file, and at a named url."""

    # check for a file path in the service settings
    pub_key_url = Config.get('web', 'apim_public_key_url')

    if pub_key_url is not None and pub_key_url != "":

        logger.info("Fetching JWT public key from \"{}\".".format(pub_key_url))

        try:
            # Fetch from the remote url
            pub_key_response = requests.get(url=pub_key_url, verify=False)

            if pub_key_response.status_code == 200:

                pub_key = pub_key_response.text

                return pub_key.strip(chars=" ")

            else:
                raise BaseAgaveflaskError(
                    msg="Error fetching JWT public key from \"{}\". {}".format(pub_key_url, pub_key_response.content),
                    code=pub_key_response.status_code)

        except Exception:

            raise BaseAgaveflaskError(msg="Unable to fetch JWT public key from \"{}\".".format(pub_key_url))

    else:
        return None



def _get_pub_key_file():
    """Read JWT public key from disk"""

    pub_key_file_path = Config.get('web', 'apim_public_key_file')

    if pub_key_file_path is not None and pub_key_file_path != "":

        f = open(pub_key_file_path, "r")

        if f.mode == 'r':
            logger.info("Reading JWT public key from disk at \"{}\".".format(pub_key_file_path))
            pub_key = f.read()
        else:
            raise BaseAgaveflaskError(
                msg="Unable to read JWT public key file from disk at \"{}\".".format(pub_key_file_path),
                code=500)

    else:
        return None

    return pub_key.strip(chars=" ")

def _get_pub_key_serialized_value():
    """Look for the JWT public key as a serialized value in the service config file."""

    pub_key = Config.get('web', 'apim_public_key')

    if pub_key is not None and pub_key != "":

        logger.info("Reading serialized JWT public key from the service config file.")

        return base64.b64decode(pub_key)

    else:
        return None

def get_pub_key():
    """Look for the jwt key in the config file, in a named file, and at a named url."""

    pub_key = _get_pub_key_serialized_value()

    if pub_key is None or pub_key == '':
        pub_key = _get_pub_key_file()

    if pub_key is None or pub_key == '':
        pub_key = _get_pub_key_url()

    if pub_key is None:
        raise BaseAgaveflaskError(msg="No JWT public key provided.", code=500)
    elif pub_key == '':
        raise BaseAgaveflaskError(msg="JWT public key was empty.", code=500)
    else:
        return RSA.importKey(pub_key)


TOKEN_RE = re.compile('Bearer (.+)')


def authn_and_authz(authz_callback=None):
    """All-in-one convenience function for implementing the basic Agave authentication
    and authorization on a flask app. Pass authz_callback, a Python callable, to do additional custom authorization
    checks within your app after the initial checks.

    Basic usage is as follows:

    import auth

    my_app = Flask(__name__)
    @my_app.before_request
    def authnz_for_my_app():
        auth.authn_and_authz()

    """
    authentication()
    authorization(authz_callback)


def authentication():
    """Entry point for authentication. Use as follows:

    import auth

    my_app = Flask(__name__)
    @my_app.before_request
    def authn_for_my_app():
        auth.authentication()

    """
    # don't control access to OPTIONS verb
    if request.method == 'OPTIONS':
        return
    access_control_type = Config.get('web', 'access_control')
    if access_control_type == 'none':
        g.user = 'anonymous'
        g.token = 'N/A'
        g.tenant = request.headers.get('tenant') or Config.get('web', 'tenant_name')
        g.api_server = get_api_server(g.tenant)
        # with access_control_type NONE, we grant all permissions:
        g.roles = ['ALL']
        return
    if access_control_type == 'jwt':
        return check_jwt(request)
    raise PermissionsError(msg='Invalid access_control')


def check_jwt(req):
    tenant_name = None
    jwt_header = None
    for k, v in req.headers.items():
        if k.startswith('X-Jwt-Assertion-'):
            tenant_name = k.split('X-Jwt-Assertion-')[1]
            jwt_header_name = k
            jwt_header = v
            break
    else:
        # never found a jwt; look for 'Assertion'
        try:
            jwt_header = req.headers['Assertion']
            jwt_header_name = 'Assertion'
            tenant_name = 'dev_staging'
        except KeyError:
            raise PermissionsError(msg='JWT header missing.')
    try:
        PUB_KEY = get_pub_key()
        decoded = jwt.decode(jwt_header, PUB_KEY)
        g.jwt_header_name = jwt_header_name
        g.jwt = jwt_header
        g.jwt_decoded = decoded
        g.tenant = tenant_name.upper()
        g.api_server = get_api_server(tenant_name)
        g.jwt_server = get_jwt_server()
        g.user = decoded['http://wso2.org/claims/enduser'].split('@')[0]
        g.token = get_token(req.headers)
    except (jwt.DecodeError, KeyError):
        logger.warn("Invalid JWT")
        raise PermissionsError(msg='Invalid JWT.')
    try:
        g.roles_str = decoded['http://wso2.org/claims/role']
    except KeyError:
        # without a roles string, we won't throw an error but will assume the user has no roles.
        logger.warn("Could not decode the roles_str from the JWT.")
        g.roles = []
        return
    # WSO2 APIM roles are returned as a single string, delineated by comma (',') characters.
    g.roles = g.roles_str.split(',')



def get_api_server(tenant_name):
    # todo - lookup tenant in tenants table
    if tenant_name.upper() == 'SANDBOX':
        return 'https://sandbox.agaveplatform.org'
    if tenant_name.upper() == 'MINIBOX':
        return 'https://minikube'
    return 'http://172.17.0.1:8000'

def get_jwt_server():
    return 'http://sandbox.agaveplatform.org'

def get_token(headers):
    """
    :type headers: dict
    :rtype: str|None
    """
    auth = headers.get('Authorization', '')
    match = TOKEN_RE.match(auth)
    if not match:
        return None
    else:
        return match.group(1)

def authorization(authz_callback=None):
    """Entry point for authorization. Use as follows:

    import auth

    my_app = Flask(__name__)
    @my_app.before_request
    def authz_for_my_app():
        auth.authorization()

    """
    if request.method == 'OPTIONS':
        # allow all users to make OPTIONS requests
        return

    if authz_callback:
        authz_callback()