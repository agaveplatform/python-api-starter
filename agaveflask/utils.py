import os
import re
from math import floor
from collections import OrderedDict
from flask import json, request, Request
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import ClientDisconnected
from flask_restful import Api
from flask_restful import reqparse

from .config import Config
from .errors import BaseAgaveflaskError

TAG = os.environ.get('service_TAG') or Config.get('general', 'TAG')


class RequestParser(reqparse.RequestParser):
    """Wrap reqparse to raise APIException."""

    def parse_args(self, *args, **kwargs):
        try:
            return super(RequestParser, self).parse_args(*args, **kwargs)
        except ClientDisconnected as exc:
            raise BaseAgaveflaskError(exc.data['message'], 400)

class AgaveApi(Api):
    """General flask_restful Api subclass for all the Agave APIs."""
    pass


def handle_error(exc):
    show_traceback = Config.get('web', 'show_traceback')
    if show_traceback == 'true':
        raise exc
    if isinstance(exc, BaseAgaveflaskError):
        response = error(msg=exc.msg)
        response.status_code = exc.code
        return response
    else:
        response = error(msg='Unrecognized exception type: {}. Exception: {}'.format(type(exc), exc))
        response.status_code = 500
        return response

def get_limit_request_parameter(query_dict={}):
    """Returns the maximum size of the response result set. If the limit parameter is present in the url
    query parameters, it will be returned as an integer value. If unspecified, the default value from the
    Config is returned. The response value will never be larger than the max_result_count value.

    :param ImmutableMultiDict query_dict:
    :return: int
    """
    max_result_count = int(Config.get('web', 'max_result_count', default_value=500))
    default_result_count = int(Config.get('web', 'default_result_count', default_value=50))

    # ensure default is not larger than max
    default_result_count = min(default_result_count, max_result_count)

    try:
        limit = query_dict.get('limit', default=default_result_count)
        if isinstance(limit, str):
            limit = "".join(limit.strip())

        if limit == '':
            return int(default_result_count)
        else:
            limit = int(limit)
            if (limit < 0):
                raise ValueError

            return min(limit, max_result_count)
    except:
        raise BaseAgaveflaskError(
            "Invalid value for 'limit.' If provided, 'limit' should be a non-negative integer value", 400)


def get_offset_request_parameter(query_dict={}):
    """Return the maximum number of results to skip in the response result set. If the offset parameter is presen
    in the url query parameters, it will be returned as an integer value. If unspecified, the default value of 0
    will be returned.

    :param ImmutableMultiDict query_dict:
    :return: int
    """
    try:
        offset = query_dict.get('offset', default=0)
        if isinstance(offset, str):
            offset = "".join(offset.strip())

        if offset == '':
            offset = 0
        else:
            offset = int(offset)
            if (offset < 0):
                raise ValueError

        return offset
    except:
        raise BaseAgaveflaskError(
            "Invalid value for 'offset.' If provided, 'offset' should be a non-negative integer value", 400)

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')

def underscoreToCamel(match):
    return match.group()[0] + match.group()[2].upper()


def camelize(data):
    if isinstance(data, dict):
        new_dict = OrderedDict()
        for key, value in data.items():
            new_key = re.sub(r"[a-z]_[a-z]", underscoreToCamel, key)
            new_dict[new_key] = camelize(value)
        return new_dict
    if isinstance(data, (list, tuple)):
        for i in range(len(data)):
            data[i] = camelize(data[i])
        return data
    return data


def camel_to_underscore(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def underscoreize(data):
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = camel_to_underscore(key)
            new_dict[new_key] = underscoreize(value)
        return new_dict
    if isinstance(data, (list, tuple)):
        for i in range(len(data)):
            data[i] = underscoreize(data[i])
        return data
    return data


def filter_snake_case(content, query_dict={}):
    """Ensures the response field names are consistently formatted in snake case if snake_case=true is
    present in the url query parameters. Otherwise the default camel case will be forced.

       :param response_data: dict|list
       :param query_dict: Dict
       :return: dict|None
    """
    try:
        snake = query_dict.get("snake_case", "false")
        if snake.lower() == "true":
            return underscoreize(content)
    except:
        pass

    return camelize(content)


def filter_naked_content(content, query_dict={}):
    """Strips the response of all but the result object when naked=true is present in the url query string.
    :param dict|list response_data:
    :param ImmutableMultiDict query_dict:
    :return: dict|None
    """
    try:
        naked = query_dict.get("naked", "false")
        if naked.lower() == "true":
            return content['result']
    except:
        pass

    return content


def filter_fields(content, query_dict={}):
    """Strips the response of all but the fields specified in the filter url query parameter. The value
    should be a comma separated list of fields given in json dot notation.

    This implementation only handles single level field names. Dot notation is not yet supported

    :param dict|list response_data:
    :param ImmutableMultiDict query_dict:
    :return: dict|None
    """

    try:
        filter = query_dict.get("filter", "")
        filter = "".join(filter.split())
        recomma = re.compile('([,]+)')
        filter = recomma.sub(',', filter)
        filter = filter.strip(',')
    except:
        return content

    # return only the matching fields if a filter was given
    if filter:
        # create equivalent sized empty object
        if isinstance(content, list):
            filter_resp = []
            for i in range(len(content)):
                filter_resp.append({})
        else:
            filter_resp = {}

        # filter field is comma separated
        filter_fields = filter.split(',')

        # for each field name given in the filter, copy that key/value to the new response content
        for field_path in filter_fields:
            if isinstance(field_path, str) and len(field_path) > 0:

                i = 0
                # if the content is a list, it must be applied to every entry
                if isinstance(content, list):
                    for item in content:
                        filter_resp[i][field_path] = item[field_path]
                else:
                    if field_path in content.keys():
                        filter_resp[field_path] = content[field_path]

        return filter_resp

    else:

        return content


def filter_pretty_print(content, query_dict={}):
    """Pretty prints the content with 2 spaces if pretty=true is present in the url query parameters.

    :param dict|list content:
    :param ImmutableMultiDict query_dict:
    :return: str
    """
    indent = None
    separators = (',', ':')

    try:
        pretty_print = query_dict.get("pretty", "false")
        if pretty_print.lower() == "true":
            indent = 2
            separators = (', ', ': ')
    except:
        pass

    return json.dumps(content, indent=indent, separators=separators)


def is_naked_response_requested(query_dict={}):
    """Returns true if naked=true is present in the url query parameters. This indicates that the standard response
    wrapper should be excluded.

    :param ImmutableMultiDict query_dict:
    :return: bool
    """
    try:
        return query_dict.get("naked", "false").lower() == "true"
    except:
        return False


def format_response(response_data, msg=None, query_dict={}):
    """Converts content to json while respecting config options. Responses will be pretty printed
    and formatted based on the query parameters. Field filtering is not performed by this function.
    :param dict|list response_data:
    :param str msg:
    :param ImmutableMultiDict query_dict:
    :return: str
    """

    content = filter_naked_content(response_data, query_dict)
    content = filter_snake_case(content, query_dict)
    content = filter_pretty_print(content, query_dict)

    return content


def ok(result, msg="The request was successful", request=request):
    response_data = {'status': 'success',
        'message': msg,
        'version': TAG,
        'result': filter_fields(result, request.args)}

    return format_response(response_data, msg=msg, query_dict=request.args)


def error(result=None, msg="Error processing the request.", request=request):
    """
    Formats and filters the result into a standard Agave API response by applying the appropriate
    naked, filter, pretty, and snake_case option.

    :param dict result:
    :param str msg:
    :param Request request:
    :return: str
    """
    response_data = {'status': 'error',
            'message': msg,
            'version': TAG,
            'result': filter_fields(result, request.args)}

    return format_response(response_data, msg=msg, query_dict=request.args)
