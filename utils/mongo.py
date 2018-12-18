import json
from flask import g
from bson import ObjectId
from bson.errors import InvalidId


class Mongo:
    def __init__(self):
        self.config = json.load(open('config.json'))
        self.MONGO_URI = self.config['mongo_uri']
        self.MONGO_DB = self.config['mongo_db']
        self.r = self.get_db()

    def get_db(self):
        if 'db' not in g:
            from pymongo import MongoClient
            g.db = MongoClient(self.MONGO_URI)[self.MONGO_DB]
        return g.db

    def insert(self, table, document):
        return self.r[table].insert_one(document)

    def table(self, table, **kwargs):
        if 'filter' in kwargs:
            k = str(kwargs.get('filter')).split("'")[1]
            v = str(kwargs.get('filter')).split("'")[3]
            documents = []
            for doc in self.r[table].find({k: v}):
                if 'id' not in doc:
                    doc['id'] = doc['_id']
                documents.append(doc)
            return documents
        documents = []
        for doc in self.r[table].find():
            if 'id' not in doc:
                doc['id'] = doc['_id']
            documents.append(doc)
        return documents

    def get(self, table, key, coerce=False):
        if coerce:
            return True if self.r[table].find_one({"id": key}) else False
        else:
            x = self.r[table].find_one({"id": key})
            if not x:
                try:
                    x = self.r[table].find_one({"_id": ObjectId(key)})
                except InvalidId:
                    x = self.r[table].find_one({"_id": key})
            return x

    def update(self, table, key, document):
        return self.r[table].update_one({"id": key}, {"$set": document})

    def delete(self, table, key):
        x = self.r[table].delete_one({"id": key})
        if x.deleted_count != 0:
            return x
        else:
            return self.r[table].delete_one({"_id": ObjectId(key)})
