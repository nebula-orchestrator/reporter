import sys, os
from pymongo import MongoClient, ASCENDING


class MongoConnection:

    # connect to db
    def __init__(self, mongo_connection_string, schema_name="nebula", max_pool_size=100):
        try:
            self.client = MongoClient(mongo_connection_string, maxPoolSize=max_pool_size)
            self.db = self.client[schema_name]
            self.collection_reports = self.db["nebula_reports"]
        except Exception as e:
            print("error connection to mongodb")
            print(e, file=sys.stderr)
            os._exit(2)

    # create TTL index
    def mongo_create_ttl_index(self, report_index_name, report_index_ttl):
        try:
            self.collection_reports.create_index([(report_index_name, ASCENDING)], background=True,
                                              name=report_index_name + "_index", unique=True, sparse=True,
                                              expireAfterSeconds=report_index_ttl)
            self.collection_reports.create_index([("device_group", ASCENDING)], background=True,
                                              name="device_group_index", unique=False, sparse=True)
            self.collection_reports.create_index([("hostname", ASCENDING)], background=True,
                                                 name="hostname_index", unique=False, sparse=True)
            self.collection_reports.create_index([("report_creation_time", ASCENDING)], background=True,
                                                 name="report_creation_time_index", unique=False, sparse=True)
        except Exception as e:
            print("error creating mongodb indexes")
            print(e, file=sys.stderr)
            os._exit(2)

    # add report
    def mongo_add_report(self, report):
        insert_id = self.collection_reports.insert_one(report).inserted_id
        return insert_id
