# 🤖 Agentic AI: Auto Talent Acquisition System

The **Agentic AI Auto Talent Acquisition System** is an intelligent recruitment platform designed to automate resume screening, candidate shortlisting, and interview scheduling. It integrates **advanced AI techniques** with enterprise tools like the **Microsoft Graph API**.

---

## 🧠 Overview

-- Leverages a **multi-agent architecture** powered by **AutoGen**.  
-- Uses models like **GPT-4** to analyze resumes and extract relevant educational data.  
-- Evaluates candidates based on user-defined academic thresholds.  
-- Sends email notifications to HR and **automatically schedules interviews** with no time conflicts.

---

## ✅ Key Functionalities

### 1. Resume Processing & Shortlisting

-- **Input**: A folder containing multiple PDF resumes.  
-- Extracts **education-related sections** from resumes.  
-- Parses name, email, phone number, academic scores.  
-- Filters candidates based on graduation percentage or other custom criteria.  
-- Shortlists qualified candidates.

### 2. Status Reporting

-- Displays statistics such as:  
   -- Total resumes analyzed  
   -- Number of shortlisted candidates  
-- Provides a **detailed view** of each shortlisted candidate’s contact info and scores.

### 3. Email Notification

-- Sends a **summary email** to HR with a list of shortlisted candidates.  
-- Uses **Microsoft Graph API** for secure and authenticated email delivery.

### 4. Interview Scheduling

-- Automatically schedules **individual interviews** for shortlisted candidates.  
-- Ensures:  
   -- Interviews are within **9:00 AM – 5:00 PM** working hours  
   -- No overlapping time slots  
   -- Each interview is **1 hour** long  
-- Sends **calendar invites via email** using Microsoft Graph API.  
-- Handles **time zone conversions** and checks admin availability.

---

## 🔁 Workflow Summary

-- **User Input**:  
   -- Folder path with resumes  
   -- Education level (e.g., graduation)  
   -- Minimum required percentage

-- **Processing Resumes**:  
   -- Reads and evaluates resumes in batches  
   -- Extracts academic data  
   -- Shortlists qualified candidates

-- **Viewing Results**:  
   -- Shows overall stats and shortlisted candidate details

-- **HR Notification**:  
   -- Sends an automated email with shortlisted names

-- **Scheduling Interviews**:  
   -- Assigns non-overlapping interview slots  
   -- Sends calendar invites to candidates

---

## ⚙️ Technologies Used

-- **AutoGen**: For multi-agent orchestration  
-- **GPT-4**: For parsing and extracting structured data from resumes  
-- **Flask + Socket.IO**: For real-time web interface  
-- **Microsoft Graph API**: For email and calendar scheduling  
-- **PyPDF2**: For reading and extracting text from PDF resumes
