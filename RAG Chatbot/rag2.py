import streamlit as st
import faiss
import numpy as np
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import requests
import json

# Function to load and split text from the uploaded fileven
def load_and_split_text(file):
    text_content = file.getvalue().decode("utf-8")  # Decode the bytes to a string
    documents = [Document(page_content=text_content)]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_documents = text_splitter.split_documents(documents)
    return split_documents

# Initialize FAISS index for storing vectors
def init_faiss_index(dim):
    index = faiss.IndexFlatL2(dim)  
    return index

def embed_and_index_documents(documents):
    embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    
    # Embed documents using the embed_documents method
    embeddings = embed_model.embed_documents([doc.page_content for doc in documents])
    
    # Convert embeddings to numpy array and check the shape
    embeddings = np.array(embeddings).astype(np.float32)

    embedding_dim = embeddings.shape[1] 
    # Get the dimensionality of the embeddings
    print("Embedding shape:--------------------------->", embeddings.shape)  
    print("embedding dimension--------->",embedding_dim)
    
    # Initialize FAISS index with the correct dimensionality if not already initialized
    if 'index' not in st.session_state:
        st.session_state.index = faiss.IndexFlatL2(embedding_dim)  # Initialize index with the correct dimensionality
    elif st.session_state.index.d != embedding_dim:
        raise ValueError("Dimensionality of new embeddings does not match existing index.")  # Raise error if dimensionality doesn't match
    
    # Add embeddings to the FAISS index
    st.session_state.index.add(embeddings)
    
    return st.session_state.index, embeddings

# Perform similarity search on the FAISS index
def search_faiss_index(query, index, embed_model):
    query_embedding = embed_model.embed_query(query)
    query_embedding = np.array(query_embedding).astype(np.float32)
    D, I = index.search(query_embedding.reshape(1, -1), k=3)  # Top 3 most similar
    return I, D

# Function to get AI response from an external API
def get_ai_response(human_message, system_message):
    API_URL = "https://api-dev.algochance.com:5002/ai-chat"
    headers = {'Content-Type': 'application/json'}
    body = {
        "human_message": human_message,
        "system_message": system_message,
        "ai_message": "",
        "parent_id": "",
        "appName": "msd",
        "projectName": "MsD"
    }
    response = requests.post(API_URL, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        data = response.json()
        return data.get("text", "No response from AI.")
    else:
        return "Error: Unable to fetch response from AI."


# Streamlit UI
st.title("AI Chatbot with Custom Documents")

# Initialize variables
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = np.empty((0, 384), dtype=np.float32)  # Initialize as an empty 2D array with 384 dimensions
if 'file_names' not in st.session_state:
    st.session_state.file_names = []
if 'message_history' not in st.session_state:
    st.session_state.message_history = []

# Initialize the index if it doesn't exist
if 'index' not in st.session_state:
    st.session_state.index = None  

# File upload and document processing
uploaded_files = st.file_uploader("Upload text files with reference data", type=["txt"], accept_multiple_files=True)

# Allow uploading up to 10 files
if uploaded_files and len(st.session_state.file_names) + len(uploaded_files) <= 10:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        if file_name not in st.session_state.file_names:
            st.session_state.file_names.append(file_name)
            # Load and split the file
            new_documents = load_and_split_text(uploaded_file)
            st.session_state.documents.extend(new_documents)
            # Embed and index new documents
            embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
            new_embeddings = embed_model.embed_documents([doc.page_content for doc in new_documents])
            new_embeddings = np.array(new_embeddings).astype(np.float32)
            
            # Ensure new_embeddings is 2D
            if new_embeddings.ndim == 1:
                new_embeddings = new_embeddings.reshape(-1, 384)
            
            # Ensure st.session_state.embeddings is 2D
            if st.session_state.embeddings.ndim == 1:
                st.session_state.embeddings = st.session_state.embeddings.reshape(-1, 384)

            # Concatenate new embeddings with the existing ones
            st.session_state.embeddings = np.concatenate([st.session_state.embeddings, new_embeddings], axis=0)

            # Initialize index if not already initialized
            if st.session_state.index is None:
                embedding_dim = new_embeddings.shape[1]  # Set dimension based on first batch
                st.session_state.index = faiss.IndexFlatL2(embedding_dim)
                print("these are the dimension ----------->", embedding_dim)  # Create index with correct dimension

            st.session_state.index.add(new_embeddings)

    st.write("Files processed and indexed successfully.")

# Display the uploaded files
if st.session_state.file_names:
    st.write("### Uploaded Files:")
    for file_name in st.session_state.file_names:
        st.write(f"- {file_name}")
        delete_button = st.button(f"Delete {file_name}")
        if delete_button:
            # Remove the file and its content from FAISS and the session state
            file_index = st.session_state.file_names.index(file_name)
            num_documents_to_remove = len([doc for doc in st.session_state.documents if doc.page_content in [doc.page_content for doc in st.session_state.documents][file_index]])  # Calculate how many docs to remove
            st.session_state.documents = st.session_state.documents[num_documents_to_remove:]
            st.session_state.embeddings = st.session_state.embeddings[num_documents_to_remove:]
            st.session_state.index = faiss.IndexFlatL2(384)  # Reinitialize the index with the correct dimension (384)
            st.session_state.index.add(st.session_state.embeddings)
            st.session_state.file_names.remove(file_name)  # Remove from file names
            st.write(f"File {file_name} deleted.")

# Input field for user's query
user_query = st.text_input("Enter your query:")

if user_query:
    if st.session_state.index is not None and st.session_state.documents:
        embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        I, D = search_faiss_index(user_query, st.session_state.index, embed_model)
        relevant_text = "\n".join([st.session_state.documents[i].page_content for i in I[0]])
        system_message = relevant_text
        st.markdown("### **System Message Sent to API**:")
        st.text(system_message)

        ai_response = get_ai_response(user_query, system_message)
        st.session_state.message_history.append({"type": "user", "message": user_query})
        st.session_state.message_history.append({"type": "ai", "message": ai_response})

    else:
        st.write("Please upload documents first and wait until they're indexed.")

# Display the chat history
for message in st.session_state.message_history:
    if message["type"] == "user":
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                <div style="background-color: darkred; color: white; padding: 10px; border-radius: 10px; max-width: 60%;">
                    {message["message"]}
                </div>
            </div>
        """, unsafe_allow_html=True)
    elif message["type"] == "ai":
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                <div style="background-color: darkgreen; color: white; padding: 10px; border-radius: 10px; max-width: 60%;">
                    {message["message"]}
                </div>
            </div>
        """, unsafe_allow_html=True)
