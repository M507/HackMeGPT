import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

# Initialize the MongoDB client
client = MongoClient(os.getenv('mongodb'))  # Replace with your MongoDB connection string
db = client["mydb"]
collection = db["good_prompts"]

# # Query the data
# cursor = collection.find({})  # You can add query conditions here if needed

e = [x['last_prompt'] for x in collection.find({})]
print(e)
# for x in collection.find({}): 
#     print(x['last_prompt'])