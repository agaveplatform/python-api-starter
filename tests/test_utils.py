
import os
import re
import base64
import pytest
from flask import json
from werkzeug.datastructures import ImmutableMultiDict

import agaveflask.auth as a
from agaveflask import utils
from agaveflask.config import Config
from agaveflask.errors import BaseAgaveflaskError


##############################################################################
#
# naked filter
#
##############################################################################

@pytest.mark.parametrize(
    "test_param_value,expected",
    [
        pytest.param("true", True, id="true"),
        pytest.param("True", True, id="True"),
        pytest.param("TRUE", True, id="TRUE"),

        pytest.param("", False, id="empty"),
        pytest.param("1", False, id="one"),
        pytest.param("0", False, id="zero"),
        pytest.param(None, False, id="None"),

        pytest.param("false", False, id="false"),
        pytest.param("False", False, id="False"),
        pytest.param("FALSE", False, id="FALSE"),
        pytest.param("foo", False, id="foo"),
    ],
)
def test_is_naked_response_requested(test_param_value, expected):

    if test_param_value is None:
        query_dict = ImmutableMultiDict(dict())
    else:
        query_dict = ImmutableMultiDict(dict(naked=test_param_value))

    assert utils.is_naked_response_requested(query_dict) == expected

@pytest.mark.parametrize(
    "test_param_value,expected",
    [
        pytest.param("true", True, id="true"),
        pytest.param("True", True, id="True"),
        pytest.param("TRUE", True, id="TRUE"),

        pytest.param("", False, id="empty"),
        pytest.param("1", False, id="one"),
        pytest.param("0", False, id="zero"),
        pytest.param(None, False, id="None"),

        pytest.param("false", False, id="false"),
        pytest.param("False", False, id="False"),
        pytest.param("FALSE", False, id="FALSE"),
        pytest.param("foo", False, id="foo"),
    ],
)
def test_filter_naked_content(test_param_value, expected):
    test_content = {'status': 'error',
                    'message': "The message succeeded",
                    'version': "testing",
                    'result': {'id': 1,
                               'name': "test_obj",
                               "owner": "testuser",
                               "_links": {"self": "http://localhost:8000/"}}}

    if test_param_value is None:
        query_dict = ImmutableMultiDict(dict())
    else:
        query_dict = ImmutableMultiDict(dict(naked=test_param_value))

    if expected:
        assert utils.filter_naked_content(test_content, query_dict) == test_content['result']
    else:
        assert utils.filter_naked_content(test_content, query_dict) == test_content


##############################################################################
#
# pretty printing filter
#
##############################################################################

@pytest.mark.parametrize(
    "test_param_value,expected",
    [
        pytest.param("true", True, id="true"),
        pytest.param("True", True, id="True"),
        pytest.param("TRUE", True, id="TRUE"),

        pytest.param("", False, id="empty"),
        pytest.param("1", False, id="one"),
        pytest.param("0", False, id="zero"),
        pytest.param(None, False, id="None"),

        pytest.param("false", False, id="false"),
        pytest.param("False", False, id="False"),
        pytest.param("FALSE", False, id="FALSE"),
        pytest.param("foo", False, id="foo"),
    ],
)
def test_filter_pretty_print(test_param_value, expected):
    test_content = {'status': 'error',
                     'message': "The message succeeded",
                     'version': "testing",
                     'result': { 'id': 1,
                                 'name': "test_obj",
                                 "owner": "testuser",
                                 "_links": { "self": "http://localhost:8000/"}}}

    separators = (',', ':')
    indent = None

    if expected:
        indent = 2
        separators = (', ', ': ')

    test_json_content = json.dumps(test_content, indent=indent, separators=separators)

    if test_param_value is None:
        query_dict = ImmutableMultiDict(dict())
    else:
        query_dict = ImmutableMultiDict(dict(pretty=test_param_value))

    assert utils.filter_pretty_print(test_content, query_dict) == test_json_content

##############################################################################
#
# snake_case filter
#
##############################################################################

@pytest.mark.parametrize(
    "test_param_value,expected",
    [
        pytest.param("true", True, id="true"),
        pytest.param("True", True, id="True"),
        pytest.param("TRUE", True, id="TRUE"),

        pytest.param("", False, id="empty"),
        pytest.param("1", False, id="one"),
        pytest.param("0", False, id="zero"),
        pytest.param(None, False, id="None"),

        pytest.param("false", False, id="false"),
        pytest.param("False", False, id="False"),
        pytest.param("FALSE", False, id="FALSE"),
        pytest.param("foo", False, id="foo"),
    ],
)
def test_filter_snake_case_handles_camel_case(test_param_value, expected):
    test_content = {'statusCode': 'success'}

    query_dict = ImmutableMultiDict(dict(snake_case=str(expected)))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():

        assert (utils.camel_to_underscore(key) in result.keys()) == expected

@pytest.mark.parametrize(
    "test_param_value,expected",
    [
        pytest.param("true", True, id="true"),
        pytest.param("True", True, id="True"),
        pytest.param("TRUE", True, id="TRUE"),

        pytest.param("", False, id="empty"),
        pytest.param("1", False, id="one"),
        pytest.param("0", False, id="zero"),
        pytest.param(None, False, id="None"),

        pytest.param("false", False, id="false"),
        pytest.param("False", False, id="False"),
        pytest.param("FALSE", False, id="FALSE"),
        pytest.param("foo", False, id="foo"),
    ],
)
def test_filter_snake_case_handles_snake_case(test_param_value, expected):
    test_content = {'status_code': 'success'}

    query_dict = ImmutableMultiDict(dict(snake_case=str(expected)))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():

        assert (re.sub(r"[a-z]_[a-z]", utils.underscoreToCamel, key) in result.keys()) != expected

def test_filter_snake_case_converts_camel_case():
    test_content = {'statusCode': 'error',
                    'messageText': "The message succeeded",
                    'apiVersion': "testing", }

    query_dict = ImmutableMultiDict(dict(snake_case="true"))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():
        assert utils.camel_to_underscore(key) in result.keys()

def test_filter_snake_case_converts_nested_camel_case():
    test_content = {'statusCode': 'error',
                    'messageText': "The message succeeded",
                    'apiVersion': "testing",
                    'result': { 'attributeA': "a", 'attributeB': "b",}}

    query_dict = ImmutableMultiDict(dict(snake_case="true"))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():
        assert utils.camel_to_underscore(key) in result.keys()

    for key in test_content['result'].keys():
        assert utils.camel_to_underscore(key) in result['result'].keys()

def test_filter_snake_case_retains_nested_snake_case():
    test_content = {'status_code': 'error',
                    'message_text': "The message succeeded",
                    'api_version': "testing",
                    'result': { 'attribute_a': "a", 'attribute_b': "b",}}

    query_dict = ImmutableMultiDict(dict(snake_case="true"))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():
        assert utils.camel_to_underscore(key) in result.keys()

    for key in test_content['result'].keys():
        assert utils.camel_to_underscore(key) in result['result'].keys()

def test_filter_snake_case_retains_snake_case():
    test_content = {'status_code': 'error',
                     'message_text': "The message succeeded",
                     'api_version': "testing",}

    query_dict = ImmutableMultiDict(dict(snake_case="true"))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():
        assert key in result.keys()


def test_filter_snake_case_converts_snake_case():
    test_content = {'status_code': 'error',
                    'message_text': "The message succeeded",
                    'api_version': "testing", }

    query_dict = ImmutableMultiDict(dict(snake_case="false"))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():
        assert re.sub(r"[a-z]_[a-z]", utils.underscoreToCamel, key) in result.keys()

def test_filter_snake_case_converts_nested_snake_case():
    test_content = {'status_code': 'error',
                    'message_text': "The message succeeded",
                    'api_version': "testing",
                    'result': { 'attribute_a': "a", 'attribute_b': "b",}}

    query_dict = ImmutableMultiDict(dict(snake_case="false"))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():
        assert re.sub(r"[a-z]_[a-z]", utils.underscoreToCamel, key) in result.keys()

    for key in test_content['result'].keys():
        assert re.sub(r"[a-z]_[a-z]", utils.underscoreToCamel, key) in result['result'].keys()

def test_filter_snake_case_retains_nested_camel_case():
    test_content = {'statusCode': 'error',
                    'messageText': "The message succeeded",
                    'apiVersion': "testing",
                    'result': { 'attributeA': "a", 'attributeB': "b",}}

    query_dict = ImmutableMultiDict(dict(snake_case="false"))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():
        assert key in result.keys()

    for key in test_content['result'].keys():
        assert key in result['result'].keys()

def test_filter_snake_case_retains_camel_case():
    test_content = {'statusCode': 'error',
                     'messageText': "The message succeeded",
                     'apiVersion': "testing",}

    query_dict = ImmutableMultiDict(dict(snake_case="false"))

    result = utils.filter_snake_case(test_content, query_dict)

    for key in test_content.keys():
        assert key in result.keys()

##############################################################################
#
# snake_case filter
#
##############################################################################

@pytest.mark.parametrize(
    "test_param_value,expected",
    [
        pytest.param("id", ['id'], id="id"),
        pytest.param("name", ['name'], id="name"),
        pytest.param("id,name", ['id','name'], id="id,name"),
        pytest.param("_links", ['_links'], id="id,name"),
        pytest.param("id,foo,name", ["id","name"], id="id,foo,name"),
    ],
)
def test_filter_fields_returns_matching_fields(test_param_value, expected):
    test_content = {'id': 1,
                   'name': "test_obj",
                   'owner': "testuser",
                   '_links': {"self": "http://localhost:8000/"}}

    query_dict = ImmutableMultiDict(dict(filter=test_param_value ))

    result = utils.filter_fields(test_content, query_dict)

    assert len(result.keys()) == len(expected)

    for key in result:
        assert key in expected
        assert result[key] == test_content[key]

@pytest.mark.parametrize(
    "test_param_value",
    [
        pytest.param("", id="empty"),
        pytest.param(" ", id="space"),
        pytest.param(",", id="comma"),
        pytest.param(", ", id="comma,space"),
        pytest.param(" ,", id="space,comma"),
        pytest.param(" , ", id="space,comma,space"),

        pytest.param(",,", id="comma,comma"),
        pytest.param(" ,,", id="space,comma,comma"),
        pytest.param(", ,", id="comma,space,comma"),
        pytest.param(",, ", id="comma,comma,space"),
        pytest.param(" , ,", id="space,comma,space,comma"),
        pytest.param(", , ", id="comma,space,comma,space"),
        pytest.param(" , , ", id="space,comma,space,comma,space"),
        pytest.param(" ,, ", id="space,comma,comma,space"),

        pytest.param(None, id="None"),

    ],
)
def test_filter_fields_returns_all_fields_on_empty_value(test_param_value):
    test_content = {'id': 1,
                   'name': "test_obj",
                   'owner': "testuser",
                   '_links': {"self": "http://localhost:8000/"}}

    query_dict = ImmutableMultiDict(dict(filter=test_param_value ))

    result = utils.filter_fields(test_content, query_dict)

    assert test_content == result

@pytest.mark.parametrize(
    "test_param_value,expected",
    [
        pytest.param("1", [], id="one"),
        pytest.param("0", [], id="zero"),
        pytest.param("false", [], id="false"),
        pytest.param("true", [], id="true"),
        pytest.param("foo", [], id="foo"),

    ],
)
def test_filter_fields_returns_empty_objects_on_no_matching_fields(test_param_value, expected):
    test_content = {'id': 1,
                   'name': "test_obj",
                   'owner': "testuser",
                   '_links': {"self": "http://localhost:8000/"}}

    query_dict = ImmutableMultiDict(dict(filter=test_param_value ))

    result = utils.filter_fields(test_content, query_dict)

    assert len(result.keys()) == 0


##############################################################################
#
# get limit request parameter
#
##############################################################################

@pytest.mark.parametrize(
    "test_param_value",
    [
        pytest.param("one", id="one"),
        pytest.param("foo", id="foo"),
        pytest.param("-1", id="-1"),
        pytest.param("true", id="true"),
        pytest.param("false", id="false"),
        pytest.param("3.14", id="3.14"),
        pytest.param(".14", id=".14"),
        pytest.param("0.14", id="0.14"),
    ],
)
def test_get_limit_request_parameter_throws_error(test_param_value):


    query_dict = ImmutableMultiDict(dict(limit=test_param_value))

    with pytest.raises(BaseAgaveflaskError):

        utils.get_limit_request_parameter(query_dict)

@pytest.mark.parametrize(
    "test_param_value,expected",
    [
        pytest.param("0", 0, id="0"),
        pytest.param("1", 1, id="1"),
    ],
)
def test_get_limit_request_parameter_returns_integer(test_param_value, expected):


    if test_param_value is None:
        query_dict = ImmutableMultiDict(dict())
    else:
        query_dict = ImmutableMultiDict(dict(limit=test_param_value))

    assert expected == utils.get_limit_request_parameter(query_dict)

@pytest.mark.parametrize(
    "test_param_value,default_result_count,expected",
    [
        pytest.param(None, "23", 23, id="None"),
        pytest.param("", "24", 24, id="empty"),
        pytest.param(" ", "25", 25, id="space"),
        pytest.param(" ", "26", 26, id="space,space"),
    ],
)
def test_get_limit_request_parameter_returns_default_result_count(test_param_value, default_result_count, expected):

    Config.set('web', 'default_result_count', default_result_count)

    if test_param_value is None:
        query_dict = ImmutableMultiDict(dict())
    else:
        query_dict = ImmutableMultiDict(dict(limit=test_param_value))

    assert expected == utils.get_limit_request_parameter(query_dict)

@pytest.mark.parametrize(
    "test_param_value,max_result_count, expected",
    [
        pytest.param("10", "8", 8, id="10>8"),
        pytest.param("8", "8", 8, id="8==8"),
        pytest.param("1", "8", 1, id="1<8"),
    ],
)
def test_get_limit_request_parameter_enforces_max_result_count(test_param_value, max_result_count, expected):

    Config.set('web', 'max_result_count', max_result_count)

    query_dict = ImmutableMultiDict(dict(limit=test_param_value))

    assert expected == utils.get_limit_request_parameter(query_dict)


##############################################################################
#
# get offset request parameter
#
##############################################################################

@pytest.mark.parametrize(
    "test_param_value",
    [
        pytest.param("one", id="one"),
        pytest.param("foo", id="foo"),
        pytest.param("-1", id="-1"),
        pytest.param("true", id="true"),
        pytest.param("false", id="false"),
        pytest.param("3.14", id="3.14"),
        pytest.param(".14", id=".14"),
        pytest.param("0.14", id="0.14"),
    ],
)
def test_get_offset_request_parameter_throws_error(test_param_value):


    query_dict = ImmutableMultiDict(dict(offset=test_param_value))

    with pytest.raises(BaseAgaveflaskError):

        utils.get_offset_request_parameter(query_dict)

@pytest.mark.parametrize(
    "test_param_value,expected",
    [
        pytest.param("0", 0, id="0"),
        pytest.param("1", 1, id="1"),
        pytest.param("100", 100, id="1"),
    ],
)
def test_get_offset_request_parameter_returns_integer(test_param_value, expected):

    query_dict = ImmutableMultiDict(dict(offset=test_param_value))

    assert expected == utils.get_offset_request_parameter(query_dict)

@pytest.mark.parametrize(
    "test_param_value",
    [
        pytest.param(None, id="None"),
        pytest.param("",   id="empty"),
        pytest.param(" ",  id="space"),
        pytest.param(" ",  id="space,space"),
    ],
)
def test_get_offset_request_parameter_returns_0(test_param_value):

    if test_param_value is None:
        query_dict = ImmutableMultiDict(dict())
    else:
        query_dict = ImmutableMultiDict(dict(offset=test_param_value))

    assert 0 == utils.get_offset_request_parameter(query_dict)
