import boto3
import time
import params
import json

RESULT_OUTPUT_LOCATION = "s3://glue-hackathon-bibichannel/athena_results/"

class ImpactAthena:
    def __init__(self, catalog_name, database_name, table_name):
        self.catalog_name = catalog_name
        self.database_name = database_name
        self.table_name = table_name
        self.ATHENA_CLIENT = boto3.client("athena")

    def get_table_metadata(self):
        response = self.ATHENA_CLIENT.get_table_metadata(
            CatalogName=self.catalog_name,
            DatabaseName=self.database_name,
            TableName=self.table_name
        )
        
        result = response['TableMetadata']['Columns']
        return list(result)

    def has_query_succeeded(self, execution_id):
        i = 0
        max_execution = 5
        
        while max_execution > 0 and i < 10:
            i += 2
            max_execution -= 1
            time.sleep(2)
            
            query_details = self.ATHENA_CLIENT.get_query_execution(
                QueryExecutionId=execution_id
            )
            state = query_details['QueryExecution']['Status']['State']
            if state == 'SUCCEEDED':
                return True
        return False

    def query(self, query):
        response = self.ATHENA_CLIENT.start_query_execution(
            QueryString=query,
            ResultConfiguration={"OutputLocation": RESULT_OUTPUT_LOCATION}
        )

        return response["QueryExecutionId"]

    def get_query_results(self, execution_id):
        response = self. ATHENA_CLIENT.get_query_results(
            QueryExecutionId=execution_id
        )

        results = response['ResultSet']['Rows']
        return results

    def get_query_error_message(self, execution_id):
        query_details = self.ATHENA_CLIENT.get_query_execution(
                QueryExecutionId=execution_id
            )
        message = query_details['QueryExecution']['Status']['StateChangeReason']
        return message


### Example
# if __name__ == "__main__":
    
    ### -------------------Create OBJ of ImpactAthena Class
    
    # obj_athena = ImpactAthena(
    #     catalog_name=params.catalog_name,
    #     database_name=params.database_name,
    #     table_name=params.table_name
    #     )
    
    ### -------------------Show metadata table
    
    # print(json.dumps(obj_athena.get_table_metadata(), indent=2))
    
    
    ### -------------------SQL Query Athena 
    
    # query_str = '''
    # SELECT
    # "candidate.contact.name" AS name,
    # "candidate.skills.technical" AS technical,
    # "candidate.skills.non-technicals" AS nonTechnical
    # FROM "customer_resume"."candidates"
    # '''
    
    # execution_id = obj_athena.query(query_str)
    # print(f"Execution id: {execution_id}")

    # query_status = obj_athena.has_query_succeeded(execution_id=execution_id)
    # print(f"Query state: {query_status}")

    # if query_status:
    #     print(obj_athena.get_query_results(execution_id=execution_id))
    # else:
    #     print(obj_athena.get_query_error_message(execution_id))