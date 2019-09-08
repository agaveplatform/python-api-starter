# This module contains classes and utilities for modeling the central objects of the business logic. Objects are
# modeled by writing a subclass of AgaveDAO equipped with a PARAMS tuple of attributes and implementations of methods
# such as get_derived_value(), get_hypermedia(), disply(), etc.

import uuid

from agaveflask.utils import RequestParser
from agaveflask.config import Config
from agaveflask.errors import DAOError


def under_to_camel(value):
    def camel_case():
        yield type(value).lower
        while True:
            yield type(value).capitalize
    c = camel_case()
    return "".join(c.__next__()(x) if x else '_' for x in value.split("_"))

def dict_to_camel(d):
    """Convert all keys in a dictionary to camel case."""
    d2 = {}
    for k,v in d.items():
        d2[under_to_camel(k)] = v
    return d2


class DbDict(dict):
    """Class for persisting a Python dictionary."""

    def __getattr__(self, key):
        # returning an AttributeError is important for making deepcopy work. cf.,
        # http://stackoverflow.com/questions/25977996/supporting-the-deep-copy-operation-on-a-custom-class
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, key, value):
        self[key] = value


class AgaveDAO(DbDict):
    """Base Data Access Object class for Agaveflask models."""

    # the parameters for the DAO
    # tuples of the form (param name, required/optional/provided/derived, attr_name, type, help, default)
    # should be defined in the subclass.
    #
    #
    # required: these fields are required in the post/put methods of the web app.
    # optional: these fields are optional in the post/put methods of the web app and have a default value.
    # provided: these fields are required to construct the DAO but are provided by the abaco client code, not the user
    #           and not the DAO class code.
    # derived: these fields are derived by the DAO class code and do not need to be passed.
    PARAMS = []

    @classmethod
    def request_parser(cls):
        """Return a flask RequestParser object that can be used in post/put processing."""
        parser = RequestParser()
        for name, source, attr, typ, help, default in cls.PARAMS:
            if source == 'derived':
                continue
            required = source == 'required'
            parser.add_argument(name, type=typ, required=required, help=help, default=default)
        return parser

    @classmethod
    def from_db(cls, db_json):
        """Construct a DAO from a db serialization."""
        return cls(**db_json)

    def __init__(self, **kwargs):
        """Construct a DAO from **kwargs. Client can also create from a dictionary, d, using AbacoDAO(**d)"""
        for name, source, attr, typ, help, default in self.PARAMS:
            if source == 'required':
                try:
                    value = kwargs[name]
                except KeyError:
                    raise DAOError("Required field {} missing".format(name))
            elif source == 'optional':
                value = kwargs.get(name, default)
            elif source == 'provided':
                try:
                    value = kwargs[name]
                except KeyError:
                    raise DAOError("Required field {} missing.".format(name))
            else:
                # derived value - check to see if already computed
                if hasattr(self, name):
                    value = getattr(self, name)
                else:
                    value = self.get_derived_value(name, kwargs)
            setattr(self, attr, value)

    def get_uuid(self):
        """Generate a random uuid."""
        return '{}-{}'.format(str(uuid.uuid1()), self.get_uuid_code())

    def get_derived_value(self, name, d):
        """Compute a derived value for the attribute `name` from the dictionary d of attributes provided."""
        raise NotImplementedError

    def case(self):
        """Convert to camel case, if required."""
        case = Config.get('web', 'case')
        if not case == 'camel':
            return self
        # if camel case, convert all attributes
        for name, _, _, _, _, _ in self.PARAMS:
            val = self.pop(name, None)
            if val is not None:
                self.__setattr__(under_to_camel(name), val)
        return self

    def get_hypermedia(self):
        """ Add the hypermedia attribute to the DAO. Subclass should override this method. """
        return {'_links': {}}

    def display(self):
        """A default display method, for those subclasses that do not define their own."""
        self.update(self.get_hypermedia())
        return self.case()