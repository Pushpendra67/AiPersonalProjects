# 💬 RAG Chatbot with Custom Document Support

The **RAG (Retrieval-Augmented Generation) Chatbot** is an interactive, real-time system that enables users to ask questions based on **their own uploaded documents**. It uses **FAISS** for fast vector search, **Hugging Face embeddings** for semantic understanding, and a custom **external AI API** for generating context-aware responses.

---

## 🧠 Overview

-- Users upload `.txt` documents for context-based conversations.  
-- Text is processed and embedded using **Hugging Face embeddings**.  
-- A **FAISS index** is built for similarity-based retrieval.  
-- Natural language queries are matched to relevant text chunks.  
-- An external API generates accurate answers using RAG-style prompting.  
-- Built using an intuitive, real-time **Streamlit interface**.

---

## ✅ Key Functionalities

### 1. Document Upload

-- Accepts up to **10 `.txt` files**.  
-- Displays a list of uploaded files.  
-- Allows individual file deletion and index updates.

### 2. Text Processing & Embedding

-- Splits documents into chunks using:  
   `RecursiveCharacterTextSplitter` (from LangChain)  
-- Embeds each chunk with:  
   `HuggingFaceEmbeddings` using `BAAI/bge-small-en-v1.5`

### 3. Vector Indexing with FAISS

-- Uses **FAISS** to store and search vector embeddings.  
-- Dynamically updates the index when documents are added/removed.  
-- Enables high-speed, top-k similarity search.

### 4. Query Handling

-- Converts user query into an embedding.  
-- Searches the FAISS index to find top **3 most similar chunks**.  
-- Constructs a prompt using the retrieved context.  
-- Sends the prompt to an external **AI API** for final answer generation.

### 5. AI-Powered Response Generation

-- Uses a **custom API** to respond with AI-generated answers:  
   `https://api-dev.algochance.com:5002/ai-chat`  
-- Maintains **conversation history** for context continuity.  
-- Returns detailed and relevant responses based on document data.

### 6. User Interface

-- Built using **Streamlit**  
-- Real-time chat with color-coded bubbles (User vs AI)  
-- Clean, minimal, and user-friendly layout

---

## 🔁 Workflow Summary

-- **Upload Documents**  
   -- User uploads `.txt` files  
   -- Text is chunked and stored  

-- **Generate Embeddings**  
   -- Each chunk is embedded using BAAI/bge-small-en-v1.5  

-- **Index Vectors**  
   -- Embeddings are stored in FAISS  

-- **User Query**  
   -- User submits a natural language question  

-- **Retrieve Relevant Context**  
   -- Top 3 matching chunks are retrieved from FAISS  

-- **Generate AI Response**  
   -- Context is sent to the API  
   -- API returns a generated response  

-- **Display Answer**  
   -- Response and history are shown in the chat window  

---

## ⚙️ Technologies Used

-- **Vector DB**: FAISS  
-- **Embeddings**: Hugging Face `BAAI/bge-small-en-v1.5`  
-- **Text Splitting**: `langchain.text_splitter.RecursiveCharacterTextSplitter`  
-- **UI Framework**: Streamlit  
-- **API Backend**:  
   `https://api-dev.algochance.com:5002/ai-chat`  
-- **Document Schema**: `langchain.schema.Document`

---

> 📚 This project brings the power of **RAG pipelines** and **user-driven context** to an easy-to-use chatbot experience. Ideal for enterprise knowledge bases, academic documents, or internal company reports.
