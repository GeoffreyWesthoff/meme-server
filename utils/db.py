import json

from flask import g
from utils.rethink import Rethink
from utils.mongo import Mongo
config = json.load(open('config.json'))


def get_db():
    if config['db'] == 'rethink':
        if 'rethink' not in g:
            g.rethink = Rethink()
        return g.rethink
    elif config['db'] == 'mongo':
        if 'mongo' not in g:
            g.mongo = Mongo()
        return g.mongo

