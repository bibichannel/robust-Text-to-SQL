import custom_athena
import interact_database
import params
import json
import boto3
from sentence_transformers import SentenceTransformer
from langchain_core.prompts import PromptTemplate
from langchain_aws import BedrockLLM

PROMPT_TMP = '''
I will provide you the schema of the "{name_table}" table in "{name_database}".
Please use the information in this schema to process my request below:

{table_metadata}

It is important that the SQL query complies with Athena syntax. 
Remember to enclose Name as a string data type in quotes.
During join, in select statement. It is also important to respect the type of columns: 
If you are writing CTEs then include all the required columns. 
While concatenating a non string column, make sure cast the column to string. 
For date columns comparing to string , please cast the string input.
Use the requirements and information provided to create an SQL query on the athena table. 
The returned results only contain the query content, no further explanation.

Requirements: {user_query}
'''


MODEL = SentenceTransformer(params.model_id)

############################## Bedrock
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1', 
)

def load_model(temperature, top_p, top_k, max_tokens):
    model_llm = BedrockLLM(
        client=bedrock_runtime,
        model_id="anthropic.claude-v2:1",
        model_kwargs={
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k, 
            "max_tokens_to_sample": max_tokens,
        }
    )
    return model_llm


def prompt_teamplate_for_generate_sql():
    prompt = PromptTemplate.from_template(
        template=PROMPT_TMP
    )
    return prompt

def extract_sql_query(response):
    query_str = response.split("```")[1]
    query_str = " ".join(query_str.split("\n")).strip()
    sql_query = query_str[3:] if query_str.startswith("sql") else query_str
    return sql_query


def execute_query(prompt, model_llm, obj_athena):
    attempt = 0
    custom_prompt = ""
    
    while attempt < 5:
        custom_prompt = prompt + custom_prompt
        with open('response_prompt.txt', 'a') as file:
            file.write(custom_prompt + '\n\n')
        
        print((f'we are in Try block to generate the sql and count is :{attempt + 1}'))

        response = model_llm.invoke(input=custom_prompt)
        with open('response_llm.txt', 'a') as file:
            file.write(response + '\n\n')
            
        query_sql = extract_sql_query(response)
        with open('response_athena.txt', 'a') as file:
            file.write(query_sql + '\n\n')
        
        execution_id = obj_athena.query(query_sql)
        print(f"Execution id: {execution_id}")

        query_status = obj_athena.has_query_succeeded(execution_id=execution_id)
        print(f"Query state: {query_status}")

        if query_status:
            result = obj_athena.get_query_results(execution_id=execution_id)
            print(f'syntax checked for query passed in attempt number :{attempt + 1}')
            print(result)
            return result
        else:
            error_message = obj_athena.get_query_error_message(execution_id)
            print(f'Syntax error in attempt number {attempt}: {error_message}')
            attempt += 1
            
            custom_prompt = f"""\nThis is syntax error: {error_message}.
            To correct this, please generate an alternative SQL query which will correct the syntax error. 
            The updated query should take care of all the syntax issues encountered. Follow the instructions mentioned above to remediate the error.
            Update the below SQL query to resolve the issue:
            {query_sql}
            Make sure the updated SQL query aligns with the requirements provided in the initial question.
            """.strip()
    return None
            

# if __name__ == "__main__":
#     obj_athena = custom_athena.ImpactAthena(
#         catalog_name=params.catalog_name,
#         database_name=params.athena_database_name,
#         table_name=params.athena_table_name
#     )

#     table_metadata = obj_athena.get_table_metadata()

#     user_query = "Statistics to see which candidate has the most skills and show the skills."

#     gen_prompt = prompt_teamplate_for_generate_sql()
#     prompt = gen_prompt.format(
#         name_database = params.athena_database_name,
#         name_table = params.athena_table_name,
#         table_metadata = str(table_metadata),
#         user_query = user_query
#     )
    
#     ### Load model & query LLM
#     model_llm = load_model(0.6, 0.7, 100, 300)
    
#     execute_query(prompt, model_llm, obj_athena)
   