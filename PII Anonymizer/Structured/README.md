# 🔐 PII Anonymizer for Structured Data

This project provides a **PII (Personally Identifiable Information) anonymization system** for structured data formats such as **CSV** and **JSON**, using the **Presidio Structured Library**. It helps protect sensitive information in datasets while retaining their analytical value.

---

## 📌 Overview

-- Supports anonymization of **CSV** and **JSON** files.  
-- Uses **Presidio’s Named Entity Recognition (NER)** engine to detect and anonymize sensitive entities.  
-- Built-in support for **Pandas-based** CSV processing and **custom JSON handlers**, including support for nested structures.  
-- Designed for **data privacy compliance**, making datasets safer for analysis and sharing.

---

## 🧩 Features

### ✅ CSV Processor

-- Reads a structured CSV file (e.g., `test_structured.csv`).  
-- Detects PII using `PandasAnalysisBuilder`.  
-- Applies anonymization with the `StructuredEngine`.  
-- Outputs a sanitized version as `anonymized_test_structured.csv`.

### ✅ JSON Processor

-- Supports both **simple and nested** JSON structures.  
-- Uses `JsonAnalysisBuilder` for analysis.  
-- Supports **manual mapping** of deeply nested fields where automatic detection is insufficient.  
-- Outputs anonymized JSON to `anonymized_sample.json`.

---

## 🧠 Entity Detection (via Presidio)

Detects the following PII types (customizable):

-- **Name** (`PERSON`)  
-- **Email** (`EMAIL_ADDRESS`)  
-- **Phone Number** (`PHONE_NUMBER`)  
-- **Location** (`LOCATION`)  
-- And more (based on Presidio recognizers)

---

> 🔒 This system is ideal for safely sharing or processing sensitive structured datasets in analytics pipelines or ML workflows.

