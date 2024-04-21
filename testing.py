import custom_athena
import interact_database
import params
import json
from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer(params.model_id)

obj_athena = custom_athena.ImpactAthena(
    catalog_name=params.catalog_name,
    database_name=params.athena_database_name,
    table_name=params.athena_table_name
    )

obj_database = interact_database.InteractDatabase(
    connect_string=params.mongodb_connect_string,
    database_name=params.mongodb_database_name,
    collection_name=params.mongodb_collection_name
)

metadata_list = obj_athena.get_table_metadata()

docs = []

for item in metadata_list:
    metadata = item["Name"]
    metadata_embedded = MODEL.encode(metadata)
    item['embedding'] = metadata_embedded.tolist()
    docs.append(item)
    
for item in docs:
    print(json.dumps(item, indent=2))

# obj_database.insert_database(docs)