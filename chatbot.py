import time
import boto3
import streamlit as st
from langchain import PromptTemplate
from langchain.chains import ConversationChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory


########### Frontend #############

INIT_MESSAGE = {
    "role": "assistant",
    "content": "Hi! I'm your AI Bot on Bedrock. How may I help you?",
}

# INIT_PROMPT_FOR_SQL + Vector Search Match Result + User Query 
INIT_PROMPT_FOR_SQL = """
    It is important that the SQL query complies with Athena syntax.
    During join, in select statement. It is also important to respect the type of columns:
    If a column is string, the value should be enclosed in quotes.
    If you are writing CTEs then include all the required columns.
    While concatenating a non string column, make sure cast the column to string.
    For date columns comparing to string , please cast the string input.
"""

def set_page_config() -> None:
    st.set_page_config(page_title="🎈 Research CV Database", layout="wide")
    st.title("🎈 Research CV Database")
    st.subheader("Chatbot with Langchain, Bedrock, and Streamlit")
    
def create_chatbot(converstation):
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

            response = converstation.invoke(input=prompt)
            
            full_response = response["response"]
            message_placeholder.markdown(full_response)
            
        st.session_state.messages.append({"role": "Assistant", "content": full_response})
        
    st.write(st.session_state)
    st.write(converstation.memory.load_memory_variables({}))


########### Backend #############

# Setup bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)

def load_model(temperature, top_p, max_tokens):
    model_llm = Bedrock(
        client=bedrock_runtime,
        model_id="anthropic.claude-v2", #amazon.titan-text-express-v1
        # model_kwargs={
        #     "temperature": temperature,
        #     "topP": top_p,
        #     "maxTokenCount": max_tokens,
        # }
        model_kwargs={
            "max_tokens_to_sample": 200,
            "temperature": 0.5,
        }
    )
    return model_llm

def create_memory():
    memory = ConversationBufferMemory()

def prompt_teamplate_for_generate_sql():
    teamplate = INIT_PROMPT_FOR_SQL + "\n{vectorSearchMatchResult}" + "\n{userQuery}"
    
    prompt = PromptTemplate(
        input_variables=["vectorSearchMatchResult","userQuery"],
        template=teamplate
    )
    return prompt

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
    model_llm = load_model(0, 1, 2048)
    converstation = create_converstaion(model_llm)
    create_chatbot(converstation)

