"""Read config files from:
- /abaco.conf (added by user)
- /etc/abaco.conf (an example is placed here by the Dockerfile)

"""

from configparser import ConfigParser
import os

HERE = os.path.dirname(os.path.abspath(__file__))

class AgaveConfigParser(ConfigParser):
    def get(self, section, option, raw=False, vars=None, default_value=None):
        try:
            return ConfigParser.get(self, section, option, raw, vars)
        except ConfigParser.NoOptionError:
            return default_value


def read_config(conf_file='service.conf'):
    parser = AgaveConfigParser()
    places = ['/{}'.format(conf_file),
              '/etc/{}'.format(conf_file),
              '{}/{}'.format(os.getcwd(), conf_file)]
    place = places[0]
    for p in places:
        if os.path.exists(p):
            place = p
            break
    else:
        raise RuntimeError('No config file found.')
    if not parser.read(place):
        raise RuntimeError("couldn't read config file from {0}"
                           .format(', '.join(place)))
    return parser

Config = read_config()