
import json
import os
import base64
import pytest
import agaveflask.auth as a
from agaveflask.config import Config

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

    try:

        pub_key = a._get_pub_key_serialized_value()

        assert pub_key is not None
        assert pub_key != ''
        assert pub_key == test_text
    except Exception:
        assert False


def test__get_pub_key_serialized_value_base64_decodes_config_value():
    test_text = b"I love cactus juice"
    encoded_text = base64.b64encode(test_text).decode('utf-8')
    Config.set('web', 'apim_public_key', encoded_text)

    try:

        pub_key = a._get_pub_key_serialized_value()

        assert pub_key is not None
        assert pub_key != ''
        assert pub_key == test_text
    except Exception:
        assert False