__import__('pysqlite3') 
import sys 
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_cohere import CohereEmbeddings
from langchain_google_genai import GoogleGenerativeAI
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Function to load and process the document
def load_and_process_document(url):
    loader = WebBaseLoader(web_path=url)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True)
    all_splits = text_splitter.split_documents(docs)
    return all_splits

# Function to initialize the retriever and LLM
def initialize_retriever_and_llm(splits):
    vectorstore = Chroma.from_documents(documents=splits, embedding=CohereEmbeddings())
    retriever = vectorstore.as_retriever(search_type="similarity")
    llm = GoogleGenerativeAI(model='gemini-1.5-pro')
    
    prompt = hub.pull('rlm/rag-prompt')
    return retriever, llm, prompt

# Function to format documents for display
def format_docs(docs):
    return '\n\n'.join(doc.page_content for doc in docs)

# Set up Streamlit app layout
st.set_page_config(page_title="Customer Support Automation", page_icon="🤖", layout="wide")

# Add custom CSS for light and dark modes and chat bubbles
st.markdown(
    """
    <style>
    :root {
        --bg-color: #ffffff;
        --text-color: #000000;
        --input-bg-color: #f0f0f0;
        --answer-bg-color: #e0e0e0;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-color: #121212;
            --text-color: #ffffff;
            --input-bg-color: #7f6ceb;
            --answer-bg-color: #2c2c2c;
        }
    }
    body {
        transition: background-color 0.5s, color 0.5s;
        background-color: var(--bg-color);
        color: var(--text-color);
    }
    .main {
        transition: background-color 0.5s, color 0.5s;
        max-width: 800px;
        margin: auto;
        padding: 2rem;
        border-radius: 10px;
        background-color: var(--input-bg-color);
        color: var(--text-color);
        max-height: 80vh;
        overflow-y: auto;
    }
    .title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: var(--text-color);
        margin-bottom: 2rem;
    }
    .input-field {
        margin-bottom: 1.5rem;
    }
    .button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
    }
    .button:hover {
        background-color: #0056b3;
    }
    .chat-bubble {
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 5px;
        background-color: var(--answer-bg-color);
        color: var(--text-color);
    }
    .user {
        background-color: #007bff;
        color: white;
        text-align: right;
    }
    .ai {
        background-color: var(--answer-bg-color);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main">', unsafe_allow_html=True)

st.markdown('<div class="title">Customer Support Automation</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">This application helps to automatically retrieve and present relevant information from a company\'s knowledge base, FAQs, or support documentation to answer customer inquiries effectively.</div>', unsafe_allow_html=True)

# URL input
url = st.text_input("Enter the URL of the knowledge base or FAQ page", key='url_input')

# Initialize session state for conversation history
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

if url:
    st.write("Loading and processing the document...")
    all_splits = load_and_process_document(url)
    
    st.write("Initializing retriever and LLM...")
    retriever, llm, prompt = initialize_retriever_and_llm(all_splits)
    
    # Define the RAG chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # User query input
    user_query = st.text_input("Enter your question", key='question_input')

    if user_query:
        st.write("Retrieving relevant information...")
        
        # Get and display the answer
        answer = rag_chain.invoke(user_query)
        
        # Save the question and answer to the conversation history
        st.session_state.conversation.append(("user", user_query))
        st.session_state.conversation.append(("ai", answer))

# Display the conversation history
for speaker, text in st.session_state.conversation:
    if speaker == "user":
        st.markdown(f'<div class="chat-bubble user">{text}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bubble ai">{text}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
