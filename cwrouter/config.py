import configparser

from os import path

config = configparser.ConfigParser()
config.read(path.expanduser('~/.cwrouter'))