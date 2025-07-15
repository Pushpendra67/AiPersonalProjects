# 📊 NLP-to-Graph Generator

The **NLP-to-Graph Generator** is an intelligent multi-agent system that enables users to create **visualizations and tables from natural language input**. Using **AutoGen**, it converts user queries into SQL, executes them on a connected database, generates Python visualization code, and returns results—all through a real-time web interface built with **Flask + Socket.IO**.

---

## 🧠 Overview

-- Accepts **natural language questions** from users.  
-- Converts input into valid **SQL queries** automatically.  
-- Executes SQL on a database and returns structured results.  
-- Translates data into **Python scripts** for visualization.  
-- Displays output as **graphs or tables** on a dynamic web frontend.  
-- Powered by a **multi-agent architecture** using AutoGen to coordinate each processing stage.

---

## ✅ Key Functionalities

### 1. Natural Language Processing (NLP)

-- Accepts user queries like:  
   _"Show me the sales trend over the last year."_  
-- Extracts intent and converts it to a structured query plan.

### 2. SQL Query Generation

-- Transforms natural language input into **accurate SQL**.  
-- Validates and auto-corrects SQL if execution errors occur.

### 3. Database Interaction

-- Executes SQL against an active **relational database** (SQLite, MySQL, PostgreSQL, etc.).  
-- Handles connection errors and malformed queries gracefully.

### 4. Data Visualization

-- Converts SQL output into Python scripts for visualizations.  
-- Supports **bar charts**, **line graphs**, **pie charts**, and **tables**.  
-- Executes Python code and captures output as images.

### 5. Interactive Web Interface

-- Uses **Flask + Socket.IO** for real-time feedback.  
-- Displays graphs and summaries **without page reloads**.  
-- Updates users as the agents progress through each step.

### 6. Custom Agent Coordination (AutoGen)

Uses AutoGen GroupChat to orchestrate specialized agents:

-- `nlptosqlagent`: Converts NLP to SQL  
-- `sqltopython`: Converts SQL output to visualization code  
-- `graph_python_code_generatorAgent`: Generates graph-drawing scripts  
-- `code_executor_agent`: Executes Python visualization scripts  
-- `summaryprovider`: Provides a natural language summary of the results  
-- `UserProxyAgent` & `LASTagent`: Manage user flow and finalization

---

## 🔁 Workflow Summary

-- **User Input**:  
   _"What are the top-selling products this quarter?"_

-- **Query Conversion**:  
   NLP is translated into an SQL query.

-- **Execution**:  
   SQL is run on the database and returns results.

-- **Visualization Code Generation**:  
   Python code is created to represent data visually.

-- **Code Execution**:  
   Python script runs and produces a graph or table image.

-- **Result Presentation**:  
   -- The visual is displayed in the UI  
   -- A text summary explains the insight in natural language

---

## ⚙️ Technologies Used

-- **Flask + Socket.IO**: Real-time web UI and communication  
-- **AutoGen**: Multi-agent coordination  
-- **LocalCommandLineCodeExecutor**: For executing Python scripts  
-- **Databases**: SQLite, MySQL, or PostgreSQL (user configurable)  
-- **Python Libraries**: Matplotlib, Pandas, CSV, Base64  
-- **Frontend**: HTML, CSS, JavaScript (Jinja templates)

---

> 💡 This project brings together **natural language understanding, databases, visualization, and real-time UI** to create a seamless, intelligent data exploration experience.
