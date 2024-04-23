import time
import boto3
import streamlit as st
import params
from custom_athena import ImpactAthena
from execute_query import execute_query, prompt_teamplate_for_generate_sql
from langchain.chains import ConversationChain
from langchain_aws import BedrockLLM
from langchain.memory import ConversationBufferMemory


########### Frontend #############

INIT_MESSAGE = {
    "role": "assistant",
    "content": "Hi! I'm your AI Bot on Bedrock. How may I help you?",
}

def set_page_config() -> None:
    st.set_page_config(page_title="🎈 Research CV Database", layout="wide")
    st.title("🎈 Research CV Database")
    st.subheader("Chatbot with Langchain, Bedrock, and Streamlit")
    
def decorate_prompt(user_query, model_llm, obj_athena):
    
    table_metadata = obj_athena.get_table_metadata()
    
    gen_prompt = prompt_teamplate_for_generate_sql()
    prompt = gen_prompt.format(
        name_database = params.athena_database_name,
        name_table = params.athena_table_name,
        table_metadata = str(table_metadata),
        user_query = user_query
    )

    respone  = execute_query(prompt, model_llm, obj_athena) 
    
    final_prompt = f'''
    I will provide you with accurate information that has been extracted from our documents.
    {respone}
    Based on the accurate information retrieved in the database above, please answer the request below.
    Requierments: {user_query}
    '''.strip()
    
    return final_prompt
    
def create_chatbot(converstation, model_llm, obj_athena):
    # Initial messages property
    if "messages" not in st.session_state:
        st.session_state.messages = [INIT_MESSAGE]
        
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Type here"):
        with st.chat_message(name="User"):
            st.markdown(prompt)
            
        st.session_state.messages.append({"role": "User", "content": prompt})
        
        with st.chat_message("Assistant"):
            message_placeholder = st.empty()
            final_prompt = decorate_prompt(prompt, model_llm, obj_athena)
            response = converstation.invoke(input=final_prompt)
            
            full_response = response["response"]
            message_placeholder.markdown(full_response)
            
        st.session_state.messages.append({"role": "Assistant", "content": full_response})
        
    # st.write(st.session_state)
    # st.write(converstation.memory.load_memory_variables({}))


########### Backend #############

# Setup bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
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

@st.cache_resource
def create_converstaion(_model_llm):
    conversation = ConversationChain(
        llm=_model_llm,
        verbose=True,
        memory=ConversationBufferMemory(human_prefix="User", ai_prefix="Assistant")
    )
    return conversation
    
if __name__ == "__main__":
    set_page_config()

    obj_athena = ImpactAthena(
        catalog_name=params.catalog_name,
        database_name=params.athena_database_name,
        table_name=params.athena_table_name
    )
    
    model_llm = load_model(0.6, 0.7, 100, 300)
    
    converstation = create_converstaion(model_llm)
    create_chatbot(converstation, model_llm, obj_athena)

