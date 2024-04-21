import params
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import MongoDBAtlasVectorSearch


# Reference: https://github.com/mongodb-developer/atlas-langchain


### Transform (Split)
docs = [
    "The students studied for their exams.",
    "Studying hard, the students prepared for their exams.",
    "The chef cooked a delicious meal.",
    "The chef cooked the chicken with the vegetables.",
    "Known for its power and aggression, Mike Tyson's boxing style was feared by many.",
]

### Embedding + Store

ATLAS_CLIENT = MongoClient(params.mongodb_connect_string)

MODEL = SentenceTransformer(params.model_id)

collection = ATLAS_CLIENT[params.db_name][params.collection_name]


def insert_database(docs):
    for doc in docs:
        doc_vector = MODEL.encode(doc)
        result_doc = {
            "sentence": doc,
            "vectorEmbedding": doc_vector.tolist(),
        }
        try:
            result = collection.insert_one(result_doc)
        except Exception as e:
            print(f"An error occurred: {e}")


def similary_search(query):
    query_vector = MODEL.encode(query)

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
    results = similary_search("The cook prepared a meal of poultry and veggies.")
    for item in results:
        print(item)
        print("\n\n---------------------\n")