import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

class MongoUp:
    def __init__(self):
        self._uri = "mongodb+srv://"+os.getenv("DB_USERNAME")+":"+ os.getenv("DB_PASSWORD")+"@"+os.getenv("DB_HOST")+"/?retryWrites=true&w=majority"
        # Create a new client and connect to the server
        self._client = None
        self.connect()

    def connect(self):
        try:
            self._client = MongoClient(self._uri, server_api=ServerApi('1'))
            self._client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

    def close(self):
        self._client.close()

    def get_collection(self, collection_name):
        return self._client.dailyreading[collection_name]

    def get_collection_names(self):
        return self._client.dailyreading.list_collection_names()  

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