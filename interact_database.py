import params
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

class InteractDatabase:
    def __init__(self, connect_string, database_name, collection_name):
        self.connect_string = connect_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.collection = None
        self.ATLAS_CLIENT =  MongoClient(connect_string)
    
    def create_collection(self):
        self.collection = self.ATLAS_CLIENT[self.database_name][self.collection_name]
        
    def insert_database(self, docs):
        for doc in docs:
            # example: doc = {"sentence": doc, "vectorEmbedding": vector.tolist())
            try:
                result = self.COLLECTION.insert_one(set(doc))
            except Exception as e:
                print(f"An error occurred: {e}")


    def similary_search(self, query_vector, collection):
        stage_search_vector = {
            "$vectorSearch": {
                "index": params.index_name,
                "path": "vectorEmbedding",
                "queryVector": query_vector.tolist(),
                "numCandidates": 10,
                "limit": 3,
            }
        }

        stage_score = {
            "$project": {
                "_id": 1,
                "sentence": 1,
                "score": {
                    "$meta": "vectorSearchScore"
                }, 
            }
        }
        
        pipeline = [stage_search_vector, stage_score]
        cursor = collection.aggregate(pipeline=pipeline)
        return list(cursor)


if __name__ == "__main__":
    obj_database = InteractDatabase(
        connect_string=params.mongodb_connect_string,
        database_name=params.mongodb_database_name,
        collection_name=params.collection_name
    )
    results = obj_database.similary_search("The cook prepared a meal of poultry and veggies.")
    for item in results:
        print(item)
        print("\n\n---------------------\n")