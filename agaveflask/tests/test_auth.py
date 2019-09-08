import base64
import pytest
import agaveflask.auth as a
from agaveflask.config import Config
from agaveflask.errors import BaseAgaveflaskError

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

def test__get_pub_key_serialized_value_returns_null_when_no_config_value():

    Config.set('web', 'apim_public_key', "")

    try:
        assert a._get_pub_key_serialized_value() is None
    except Exception:
        assert False

def test__get_pub_key_serialized_value_base64_decodes_config_value():
    test_text = b"I love cactus juice"
    encoded_text = base64.b64encode(test_text).decode('utf-8')
    Config.set('web', 'apim_public_key', encoded_text)

    pub_key = a._get_pub_key_serialized_value()

    assert pub_key is not None
    assert pub_key != ''
    assert pub_key == test_text

@pytest.mark.parametrize(
    "test_http_code",
    [
        pytest.param(400, id="400"),
        pytest.param(401, id="401"),
        pytest.param(403, id="403"),
        pytest.param(404, id="404"),
        pytest.param(500, id="500"),
    ],
)
def test__get_pub_key_url_throws_exception(test_http_code):

    test_url = "https://httpbin.agaveplatform.org/status/{}".format(test_http_code)
    Config.set('web', 'apim_public_key_url', test_url)

    with pytest.raises(BaseAgaveflaskError):
        try:
            pub_key = a._get_pub_key_url()
        except BaseAgaveflaskError as err:
            assert err.code == test_http_code
            raise err

def test__get_pub_key_url_fetches_value():
    test_key = b'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCUp/oV1vWc8/TkQSiAvTousMzO\nM4asB2iltr2QKozni5aVFu818MpOLZIr8LMnTzWllJvvaA5RAAdpbECb+48FjbBe\n0hseUdN5HpwvnH/DW8ZccGvk53I6Orq7hLCv1ZHtuOCokghz/ATrhyPq+QktMfXn\nRS4HrKGJTzxaCcU7OQIDAQAB'

    test_url = "https://httpbin.org/base64/{}".format(base64.urlsafe_b64encode(test_key).decode('utf-8'))
    Config.set('web', 'apim_public_key_url', test_url)

    pub_key = a._get_pub_key_url()

    assert pub_key is not None
    assert pub_key != ''
    assert pub_key == base64.b64decode(test_key)


def test__get_pub_key_file_returns_null_when_no_config_value():
    Config.set('web', 'apim_public_key_file', "")
    assert a._get_pub_key_file() is None



def test__gepub_key_filet_pub_key_file_returns_null_when_path_does_not_exist():
    Config.set('web', 'apim_public_key_file', "/dev/null/this/does/not/exist")

    with pytest.raises(BaseAgaveflaskError):
        try:
            a._get_pub_key_file()
        except BaseAgaveflaskError as err:
            assert err.code == 500
            raise err

def test__get_pub_key_file_returns_empty_when_file_is_empty(tmpdir):
    pub_key_file = tmpdir.mkdir("certs").join("cert.pem")
    pub_key_file.write_binary(b'')

    Config.set('web', 'apim_public_key_file', pub_key_file.strpath)

    pub_key = a._get_pub_key_file()

    assert pub_key is b''


def test__get_pub_key_file_fetches_value(tmpdir):
    test_key = b'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCUp/oV1vWc8/TkQSiAvTousMzO\nM4asB2iltr2QKozni5aVFu818MpOLZIr8LMnTzWllJvvaA5RAAdpbECb+48FjbBe\n0hseUdN5HpwvnH/DW8ZccGvk53I6Orq7hLCv1ZHtuOCokghz/ATrhyPq+QktMfXn\nRS4HrKGJTzxaCcU7OQIDAQAB'
    pub_key_file = tmpdir.mkdir("certs").join("cert.pem")
    pub_key_file.write_binary(test_key)

    Config.set('web', 'apim_public_key_file', pub_key_file.strpath)

    pub_key = a._get_pub_key_file()

    assert pub_key is not None
    assert pub_key != ''
    assert pub_key == base64.b64decode(test_key)


def load_jwt_pub_key(pub_key_content):
    return serialization.load_ssh_public_key(pub_key_content, backend=default_backend())

def test__get_pub_key_honors_serialized_value_precedence(tmpdir):
    test_key = b'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCUp/oV1vWc8/TkQSiAvTousMzO\nM4asB2iltr2QKozni5aVFu818MpOLZIr8LMnTzWllJvvaA5RAAdpbECb+48FjbBe\n0hseUdN5HpwvnH/DW8ZccGvk53I6Orq7hLCv1ZHtuOCokghz/ATrhyPq+QktMfXn\nRS4HrKGJTzxaCcU7OQIDAQAB'
    fake_key = b'not the key'

    pub_key_file = tmpdir.mkdir("certs").join("cert.pem")
    pub_key_file.write_binary(fake_key)

    test_url = "https://httpbin.org/base64/{}".format(base64.urlsafe_b64encode(fake_key).decode('utf-8'))

    Config.set('web', 'apim_public_key', test_key.decode('utf-8'))
    Config.set('web', 'apim_public_key_file', pub_key_file.strpath)
    Config.set('web', 'apim_public_key_url', test_url)

    pub_key = a.get_pub_key()

    assert pub_key == base64.b64decode(test_key)