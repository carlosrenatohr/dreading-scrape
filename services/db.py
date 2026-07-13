import logging
import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

logger = logging.getLogger(__name__)

class MongoUp:
    def __init__(self):
        # Prefer a full connection string (e.g. mongodb://mongo:27017 for the local
        # Docker stack); fall back to building an Atlas mongodb+srv URI from parts.
        self._uri = os.getenv("DB_URI") or (
            "mongodb+srv://" + os.getenv("DB_USERNAME", "") + ":" + os.getenv("DB_PASSWORD", "")
            + "@" + os.getenv("DB_HOST", "") + "/?retryWrites=true&w=majority"
        )
        self._db_name = os.getenv("DB_NAME", "dailyreading")
        # Create a new client and connect to the server
        self._client = None
        self.connect()

    def connect(self):
        try:
            self._client = MongoClient(self._uri, server_api=ServerApi('1'))
            self._client.admin.command('ping')
            logger.info("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception:
            # Fail loudly: previously the exception was swallowed and `_client`
            # was left None, so later calls crashed with AttributeError and a
            # broken run could still exit 0. Re-raise so the run exits non-zero.
            logger.exception("Failed to connect to MongoDB")
            raise

    def close(self):
        self._client.close()

    def get_collection(self, collection_name):
        return self._client[self._db_name][collection_name]

    def get_collection_names(self):
        return self._client[self._db_name].list_collection_names()

    def post_doc(self, collection_name, doc):
        # connect()
        collection = self.get_collection(collection_name)
        inserted_id = collection.insert_one(doc).inserted_id
        # self.close()
        return inserted_id
        
    def get_doc(self, collection_name, query):
        # connect()
        collection = self.get_collection(collection_name)
        doc = collection.find_one(query)
        # self.close()
        return doc.get('_id') if doc else None