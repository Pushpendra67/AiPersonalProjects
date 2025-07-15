# 🛒 Autonomous Store Management System

The **Autonomous Store Management System** is an AI-driven, multi-agent system that simulates a fully automated customer experience for a commodity store (e.g., wheat, rice, pulses). Built using **AutoGen**, it automates the complete pipeline from product browsing to delivery and feedback.

---

## 🧠 Overview

-- Designed to simulate a **storefront assistant** using a team of intelligent agents.  
-- Each agent handles a specific stage of the interaction flow—**product display**, **order processing**, **delivery coordination**, and **feedback collection**.  
-- The conversation is orchestrated using **AutoGen's GroupChatManager**, enabling seamless agent collaboration and context sharing.

---

## ✅ Key Functionalities

### 1. Product Display

-- Shows a list of available commodities (e.g., wheat, rice, pulses).  
-- Provides detailed information:  
   -- Product name  
   -- Price per unit  
   -- Discount (if applicable)  
   -- Expiry date or shelf life

### 2. Order Processing

-- Collects product selections and desired quantities from the user.  
-- Applies discounts automatically.    
-- Confirms the order.

### 3. Delivery Management

-- Gathers delivery address from the customer.  
-- Calculates delivery charges based on distance or store policy.  
-- Confirms delivery.

### 4. Feedback Collection

-- Prompts the user for feedback about their experience.  
-- stores feedback for future analysis or dashboarding.

---

## 🔁 Workflow Summary

-- **Customer Interaction Begins**:  
   -- User initiates interaction by asking to view products.

-- **Product Display**:  
   -- `ProductShowingAgent` lists items with prices and details.

-- **Order Placement**:  
   -- `OrderProcessingAgent` handles product selection and payment.

-- **Delivery Setup**:  
   -- `DeliveryAgent` collects address and confirms shipment.

-- **Feedback Request**:  
   -- `FeedbackAgent` gathers customer feedback after delivery.

-- **Termination**:  
   -- Conversation ends with a thank-you message and optional feedback summary.

---

## ⚙️ Technologies Used

-- **AutoGen**: Core multi-agent orchestration framework.  
-- **Azure OpenAI API**: GPT-4 for natural language understanding and generation.  
-- **JSON**: Used to store and retrieve product data dynamically.

---

> 🧠 This project demonstrates how multi-agent AI systems can replicate complex, human-like service workflows in real-world scenarios like e-commerce and logistics.
