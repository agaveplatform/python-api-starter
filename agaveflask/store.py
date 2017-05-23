
import collections
from datetime import datetime
import json

import configparser
import redis
from pymongo import MongoClient

from config import Config


def _do_get(getter, key):
    obj = getter(key)
    if obj is None:
        raise KeyError('"{}" not found'.format(key))
    try:
        return json.loads(obj.decode('utf-8'))
    # handle non-JSON data
    except ValueError:
        return obj.decode('utf-8')


def _do_set(setter, key, value):
    obj = json.dumps(value)
    setter(key, obj.encode('utf-8'))

class StoreMutexException(Exception):
    pass


class AbstractStore(collections.MutableMapping):
    """A persitent dictionary."""

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def __iter__(self):
        """Iterator for the keys."""
        pass

    def __len__(self):
        """Size of db."""
        pass

    def set_with_expiry(self, key, obj):
        """Set `key` to `obj` with automatic expiration of the configured seconds."""
        pass

    def update(self, key, field, value):
        "Atomic ``self[key][field] = value``."""
        pass

    def pop_field(self, key, field):
        "Atomic pop ``self[key][field]``."""
        pass

    def update_subfield(self, key, field1, field2, value):
        "Atomic ``self[key][field1][field2] = value``."""
        pass

    def getset(self, key, value):
        "Atomically: ``self[key] = value`` and return previous ``self[key]``."
        pass

    def mutex_acquire(self, key):
        """Try to use key as a mutex.
        Raise StoreMutexException if not available.
        """

        busy = self.getset(key, True)
        if busy:
            raise StoreMutexException('{} is busy'.format(key))

    def mutex_release(self, key):
        self[key] = False


class AbstractTransactionalStore(AbstractStore):
    """Adds basic transactional semantics to the AbstractStore interface."""
    def within_transaction(self, f, key):
        """Execute a callable, f, within a lock on key `key`."""
        pass

class RedisStore(AbstractStore):

    def __init__(self, host, port, db=0):
        self._db = redis.StrictRedis(host=host, port=port, db=db)
        try:
            self.ex = int(Config.get('web', 'log_ex'))
        except ValueError:
            self.ex = -1

    def __getitem__(self, key):
        return _do_get(self._db.get, key)

    def __setitem__(self, key, value):
        _do_set(self._db.set, key, value)

    def __delitem__(self, key):
        self._db.delete(key)

    def __iter__(self):
        return self._db.scan_iter()

    def __len__(self):
        return self._db.dbsize()

    def set_with_expiry(self, key, obj):
        """Set `key` to `obj` with automatic expiration of `ex` seconds."""
        self._db.set(key, obj, ex=self.ex)

    def update(self, key, field, value):
        "Atomic ``self[key][field] = value``."""

        def _update(pipe):
            cur = _do_get(pipe.get, key)
            cur[field] = value
            pipe.multi()
            _do_set(pipe.set, key, cur)

        self._db.transaction(_update, key)

    def pop_field(self, key, field):
        "Atomic pop ``self[key][field]``."""

        # Note: it is problematic to return items from within the _db.transaction() wrapper, as these
        # We initially had the following implementation, but it did not work: the value returned was a list of
        # results returned from the redis pipe (e.g. [True]) instead of the actual return value.
        #     def _pop(pipe):
        #         cur = _do_get(pipe.get, key)
        #         value = cur.pop(field)
        #         pipe.multi()
        #         _do_set(pipe.set, key, cur)
        #         return value
        #
        #     return self._db.transaction(_pop, key)

        with self._db.pipeline() as pipe:
            while 1:
                try:
                    pipe.watch(key)
                    cur = _do_get(pipe.get, key)
                    value = cur.pop(field)
                    _do_set(pipe.set, key, cur)
                    pipe.execute()
                    return value
                except redis.WatchError:
                    continue

    def update_subfield(self, key, field1, field2, value):
        "Atomic ``self[key][field1][field2] = value``."""

        def _update(pipe):
            cur = _do_get(pipe.get, key)
            cur[field1][field2] = value
            pipe.multi()
            _do_set(pipe.set, key, cur)

        self._db.transaction(_update, key)

    def getset(self, key, value):
        "Atomically: ``self[key] = value`` and return previous ``self[key]``."

        value = self._db.getset(key, json.dumps(value).encode('utf-8'))
        if value is not None:
            return json.loads(value.decode('utf-8'))

    def add_if_empty(self, key, field, value):
        """
        Atomic ``self[key][field] = value`` if s``self[key]`` does not exist or is empty.
        Add a value, `value`, to a field, `field`, under key, `key`, only if the key does not exist
        or it's value is currently empty. Returns the value if it was added; otherwise, returns None.
        """
        def _transaction(pipe):
            try:
                cur = _do_get(pipe.get, key)
                if cur is None or cur == {}:
                    cur[field] = value
                    pipe.multi()
                    _do_set(pipe.set, key, cur)
                    return value
                else:
                    return None
            except KeyError:
                # if the key doesn't exist at all, go ahead and set the value.
                obj = {field: value}
                pipe.multi()
                _do_set(pipe.set, key, obj)
            # the key exists in the store; if it is the value empty, and the field:
        return self._db.transaction(_transaction, key)

    def within_transaction(self, f, key):
        """Execute a callable, f, within a lock on key `key`. The executable, f, should take a single argument that
        is the current value under the key """
        def _transaction(pipe):
            cur = _do_get(pipe.get, key)
            f(cur)

        return self._db.transaction(_transaction, key)


class MongoStore(AbstractStore):

    def __init__(self, host, port, database='abaco', db='0'):
        """
        Creates an abaco `store` which maps to a single mongo
        collection within some database.
        :param host: the IP address of the mongo server.
        :param port: port of the mongo server.
        :param database: the mongo database to use for abaco.
        :param db: an integer mapping to a mongo collection within the
        mongo database.

        :return:
        """
        mongo_uri = 'mongodb://{}:{}'.format(host, port)
        self._mongo_client = MongoClient(mongo_uri)
        self._mongo_database = self._mongo_client[database]
        self._db = self._mongo_database[db]

    def __getitem__(self, key):
        result = self._db.find_one({'_id': key})
        if not result:
            raise KeyError()
        return result[key]

    def __setitem__(self, key, value):
        self._db.save({'_id': key, key: value})

    def __delitem__(self, key):
        self._db.delete_one({'_id': key})

    def __iter__(self):
        for cursor in self._db.find():
            yield cursor['_id']
        # return self._db.scan_iter()

    def __len__(self):
        return self._db.count()

    def _prepset(self, value):
        if type(value) is bytes:
            return value.decode('utf-8')
        return value

    def set_with_expiry(self, key, obj):
        """Set `key` to `obj` with automatic expiration of the configured seconds."""
        self._db.save({'_id': key, 'exp': datetime.utcnow(), key: self._prepset(obj)})

    def update(self, key, field, value):
        "Atomic ``self[key][field] = value``."""
        result = self._db.find_and_modify(query={'_id': key},
                                          update={'$set': {'{}.{}'.format(key,field): value}})
        if not result:
            raise KeyError()

    def pop_field(self, key, field):
        "Atomic pop ``self[key][field]``."""
        result = self._db.find_and_modify(query={'_id': key},
                                          update={'$unset': {'{}.{}'.format(key, field): ''}})
        result = result.get(key)
        return result[field]

    def update_subfield(self, key, field1, field2, value):
        "Atomic ``self[key][field1][field2] = value``."""
        self._db.update_one({'_id': key}, {'$set': {'{}.{}.{}'.format(key, field1, field2): value}})

    def getset(self, key, value):
        "Atomically: ``self[key] = value`` and return previous ``self[key]``."
        value = self._db.find_and_modify(query={'_id': key},
                                         update={key: value})
        return value[key]