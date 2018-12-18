import json


class Rethink:
    def __init__(self):
        self.config = json.load(open('config.json'))
        import rethinkdb as r
        self.r = r
        self.RDB_ADDRESS = self.config['rdb_address']
        self.RDB_PORT = self.config['rdb_port']
        self.RDB_DB = self.config['rdb_db']

    def get_db(self):
        if 'db' not in g:
            g.db = self.r.connect(self.RDB_ADDRESS, self.RDB_PORT, db=self.RDB_DB)
        return g.db

    def insert(self, table, document):
        return self.r.table(table).insert(document).run(self.get_db())

    def table(self, table, **kwargs):
        if 'filter' in kwargs:
            return self.r.table(table).filter(kwargs.get('filter')).run(self.get_db())
        return self.r.table(table).run(self.get_db())

    def get(self, table, key, coerce=False):
        if coerce:
            return self.r.table(table).get(key).coerce_to('bool').default(False).run(self.get_db())
        else:
            return self.r.table(table).get(key).run(self.get_db())

    def update(self, table, key, document):
        return self.r.table(table).get(key).update(document).run(self.get_db())

    def delete(self, table, key):
        return self.r.table(table).get(key).delete().run(self.get_db())
