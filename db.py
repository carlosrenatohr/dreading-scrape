import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

uri = "mongodb+srv://admin:"+ os.getenv("DB_PASSWORD")+"@dailyreading.1mgkwkx.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection

def connect():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(e)

def get_collection(collection_name):
    return client.dailyreading[collection_name]

def get_collection_names():
    return client.dailyreading.list_collection_names()  

def post_doc(collection_name, doc):
    collection = get_collection(collection_name)
    inserted_id = collection.insert_one(doc).inserted_id
    return inserted_id