# 🤖 Autonomous Food Delivery System (Built with MagenticOne)

The **Autonomous Food Delivery System** is an agentic AI solution designed to automate the end-to-end food delivery planning process. Built using **MagenticOne** and **AutoGen**, it understands natural language commands, builds execution plans, and delegates tasks to specialized agents—completing operations with minimal human intervention.

---

## 🧠 Overview

-- Uses **autonomous agents** to understand and plan food delivery tasks.  
-- Capable of searching web data, generating and executing automation code, and managing files.  
-- Powered by the **MagenticOneGroupChat** system for intelligent task orchestration.  
-- Provides **real-time feedback** to users via a web interface.

---

## ✅ Key Functionalities

### 1. Natural Language Task Processing

-- Accepts free-form user commands (e.g., _"Find the fastest delivery route from XYZ to ABC"_).  
-- Parses input to determine user intent and task scope.

### 2. Agent-Based Task Orchestration

Uses a specialized team of agents to complete subtasks:

-- **Multimodal WebSurfer**: Searches the web for food delivery options, maps, and reviews.  
-- **AssistantAgent**: Helps decompose and manage complex tasks.  
-- **FileSurfer**: Interacts with local files and logs.  
-- **MagenticOneCoderAgent**: Generates automation code for delivery operations.  
-- **CodeExecutorAgent**: Runs the generated code using local shell commands.

### 3. Real-Time Communication via WebSockets

-- Uses **Flask + Socket.IO** to provide live updates on agent activity.  
-- Users can track execution steps, agent coordination, and final output in real time.

### 4. Task Planning and Execution

-- The **MagenticOneGroupChat** orchestrates all agents seamlessly.  
-- Automatically builds an execution plan.  
-- Ensures agents collaborate in sequence and share context without manual syncing.

---

## 🔁 Workflow Summary

-- **User Input**:  
   -- Enter a task via web UI (e.g., _"Find the top-rated pizza delivery near me"_).

-- **Task Understanding**:  
   -- The system parses the query and identifies the necessary agents.

-- **Plan Creation**:  
   -- MagenticOne creates a step-by-step task plan.

-- **Agent Coordination**:  
   -- Activates agents in the right order to complete subtasks.

-- **Execution & Feedback**:  
   -- Performs actions like web search, file operations, and code execution.  
   -- Sends real-time updates to the frontend.

-- **Result Delivery**:  
   -- Compiles and displays results to the user.

---

## ⚙️ Technologies Used

-- **AutoGen**: Multi-agent framework for building intelligent systems.  
-- **MagenticOne**: Natural language planner and agent orchestrator.  
-- **Flask + Socket.IO**: Backend and real-time communication.  
-- **Azure OpenAI (GPT-4o)**: Large language model behind reasoning agents.  
-- **MultimodalWebSurfer**: Agent for online data collection.  
-- **LocalCommandLineCodeExecutor**: For running code in a secure shell environment.
