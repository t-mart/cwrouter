import errno
import json
import os
import sys

from cwrouter import __version__
from cwrouter.stats import Stats

is_windows = 'win32' in str(sys.platform).lower()

DEFAULT_CONFIG_DIR = os.environ.get(
        'CWROUTER_CONFIG',
        os.path.expanduser('~/.cwrouter') if not is_windows else
        os.path.expandvars(r'%APPDATA%\\cwrouter')
)


def ensure_config_dir_exists():
    try:
        os.makedirs(DEFAULT_CONFIG_DIR, mode=0o700)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


class BaseConfigDict(dict):
    name = None
    about = None

    def __getattr__(self, item):
        return self[item]

    @property
    def path(self):
        """Return the config file path creating basedir, if needed."""
        ensure_config_dir_exists()
        return self._path

    def is_new(self):
        return not os.path.exists(self.path)

    def load(self):
        try:
            with open(self.path, 'r') as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    raise ValueError(
                            'Invalid %s JSON: %s [%s]' %
                            (type(self).__name__, str(e), self.path)
                    )
                self.update(data)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

    def save(self):
        self['__meta__'] = {
            'cwrouter': __version__
        }

        if self.about:
            self['__meta__']['about'] = self.about

        with open(self.path, 'w') as f:
            json.dump(self, f, indent=4, sort_keys=True, ensure_ascii=True)
            f.write('\n')

    def delete(self):
        try:
            os.unlink(self.path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def last_stats(self):
        return Stats(self['last_stats']['recv_bytes'], self['last_stats']['sent_bytes'])

    def update_last_stats(self, stats):
        self['last_stats'].update({
            'recv_bytes': stats.recv_bytes,
            'total_bytes': stats.total_bytes,
            'sent_bytes': stats.sent_bytes
        })


class Config(BaseConfigDict):
    about = 'cwrouter configuration file'
    name = 'config'

    DEFAULTS = {
        'aws_secret_access_key': 'fill_in',
        'aws_access_key_id': 'fill_in',
        'stats_url': 'http://192.168.1.254/cgi-bin/dslstatistics.ha',
        'last_stats': {'recv_bytes': None, 'sent_bytes': None, 'total_bytes': None},
        'namespace': 'cwrouter',
    }

    def __init__(self, directory=DEFAULT_CONFIG_DIR):
        super(Config, self).__init__()
        self.update(self.DEFAULTS)
        self.directory = directory
        self._path = os.path.join(directory, self.name + ".json")
