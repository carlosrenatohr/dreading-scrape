import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

uri = "mongodb+srv://"+os.getenv("DB_USERNAME")+":"+ os.getenv("DB_PASSWORD")+"@"+os.getenv("DB_HOST")+"/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

def connect():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(e)

def close():
    client.close()

def get_collection(collection_name):
    return client.dailyreading[collection_name]

def get_collection_names():
    return client.dailyreading.list_collection_names()  

def post_doc(collection_name, doc):
    connect()
    collection = get_collection(collection_name)
    inserted_id = collection.insert_one(doc).inserted_id
    close()
    return inserted_id
    