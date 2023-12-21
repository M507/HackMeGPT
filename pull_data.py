import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

# Initialize the MongoDB client
client = MongoClient(os.getenv('mongodb'))  # Replace with your MongoDB connection string
db = client["mydb"]
collection = db["user_requests"]

# Query the data
cursor = collection.find({})  # You can add query conditions here if needed

# Iterate through the results and print the data
for document in cursor:
    print(document)