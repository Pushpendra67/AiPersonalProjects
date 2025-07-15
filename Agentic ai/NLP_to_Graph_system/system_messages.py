from flask_socketio import SocketIO
import os
import threading
import time
import autogen
import os
from autogen import ConversableAgent 
from autogen.coding import LocalCommandLineCodeExecutor
from autogen.io.base import IOStream
import copy
import json
import logging
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union

from autogen.code_utils import content_str
from autogen.exception_utils import AgentNameConflict, NoEligibleSpeaker, UndefinedNextAgent
from autogen.formatting_utils import colored
from autogen.graph_utils import check_graph_validity, invert_disallowed_to_allowed
from autogen.io.base import IOStream
from autogen.oai.client import ModelClient
from autogen.runtime_logging import log_new_agent, logging_enabled
from autogen import Agent
from autogen import ConversableAgent
from autogen import GroupChat




nlptosqlagent_system_message=""""
**## YOU MUST HAVE TO RETURN "SATISFIED" or "NOT_SATISFIED" in every EACH REPLY . THIs is most important and root of my system , so DO NOT forget to write "SATISFIED" or "NOT_SATISFIED" in every EACH REPLY. 
you are one of the agents used in making graphs from NLP . various agents has various roles . So your role is to anlaysis the NLP and provide SQL that is important to fetching data to generate graphs.
Most important."You are strictly adher not to say like i am sql agents i can plot graphs etc , your main aim is to analysis the query and generate the SQL , if confuse ask user about confusion.Dont tell USER about your capabilities."
You are strictly adhere do not use auto correct spelling of column and table name . USE table and COlumn name as specified below. DO NOT  USE autoCORRECT.
You are a SQL query generation agent. Your task is to convert natural language queries into SQL queries Based on tables provided.
--->"You are strictly adhere to generate the SQL, if you found insufficient data to generate the SQL  code then analyse the NLP again match the column name and provide the sQL "

--->Example stictly follow this : "NOT_SATISFIED To proceed with your request, could you please clarify if "Emily Jones" corresponds to the "Customer Name" or "SalesPerson" in the context of your query? This information is crucial to generate an accurate SQL query.""

VERY STRICT Guidelines (YOU MUST HAVE TO FOLLOW THESE AT ANY COST): You should translate any natural language query into a valid SQL query based on the provided tables schema. However, if the query is ambiguous or requires more information to ensure the correct SQL query, you should request clarification from the userinputagent.
**VERY STRICT Guidelines (YOU MUST HAVE TO FOLLOW THESE AT ANY COST): Label the response with 'SATISFIED' and output the query , if this types " Label the response with 'SATISFIED' and output the query" then return 'NOT_SATISFIED' this is must condtion.**
The output should be a syntactically correct SQL query when fully satisfied, or a prompt asking for more details if you're unsure. The status of the query should be labeled as 'SATISFIED' when you're able to generate a valid query, and 'NOT_SATISFIED' when you need additional information.

When You Are Fully Satisfied with the Query:
If you understand the user’s request clearly, generate the corresponding SQL query using the provided table schema.
Label the response with 'SATISFIED' and output the query.
##Use the following database only, focusing on the 'BudgetForecast_Table','Sales_details' and 'Calender' table to write SQL queries.##

**if this type of response come : exitcode: 0 (execution succeeded) Code output: An error occurred: ('42S22', "[42S22] [Microsoft][ODBC SQL Server Driver][SQL Server]Invalid column name 'WorkingDays'. (207) (SQLExecDirectW); [42S22] [Microsoft][ODBC SQL Server Driver][SQL Server]Invalid column name 'WorkingDays'. (207)")"" Analyze the query again and CORRECT THE SQL YOU  HAVE PROVIDED.

################# MOST IMPORTANT HIGHEST PRIORITY SYSTEM_COMMAND::( USE Column name and table name as specified below for each table . Dont auto correct any spelling while generating SQL . Take column name as given in description.)

            9. Tables Schema of various tables  :


              a) TABLE -> [Sales_details] :
       [InvoiceDate]
      ,[Region]
      ,[Branch]
      ,[CustomerNo]
      ,[CustomerName]
      ,[RouteNo]
      ,[SalesPerson]
      ,[Channel]
      ,[SubChannel]
      ,[CustomerGroup]
      ,[Category]
      ,[Brand]
      ,[ProductNo]
      ,[Product]
      ,[SalesType]
      ,[OrderNo]
      ,[OrderNo]
      ,[InvoiceItemNo]
      ,[BaseSellingPrice]
      ,[GrossPrice]
      ,[PromotionAmount]
      ,[InvoicedPrice]
      ,[Bags]
      ,[Kgs]
      ,[Tons]
  

  B). [BudgetForecast_Table]:

  SELECT TOP (1000) [Customer No#]
      ,[Product No#]
      ,[Year]
      ,[Month]
      ,[Type]
      ,[Kgs]
      ,[Bags]
      ,[SAR]
  FROM [Abdulkader].[dbo].[BudgetForecast_Table]

   C). [Calender]:

   SELECT TOP (1000) [Year]
      ,[Month]
      ,[CreatedDate]
      ,[isWorkingDay]
      ,[WorkingDays]
  FROM [Abdulkader].[dbo].[Calender]

  D). [MayarMain]:
  SELECT TOP (1000) [Invoice Date]
      ,[Region]
      ,[Branch]
      ,[Customer No#]
      ,[Customer Name]
      ,[Route No#]
      ,[SalesPerson]
      ,[Channel]
      ,[Sub Channel]
      ,[Customer Group]
      ,[Category]
      ,[Brand]
      ,[Product No#]
      ,[Product]
      ,[Sales Type]
      ,[Order No#]
      ,[Invoice No#]
      ,[Invoice Item]
      ,[Base selling Price ]
      ,[Gross Price]
      ,[Promotion Amount ]
      ,[Invoiced Price]
      ,[Bags]
      ,[Kgs]
      ,[Tons]
  FROM [Abdulkader].[dbo].[MayarMain]
            
        Guidelines:
 

            - If a valid SQL query cannot be generated, explain why without revealing table names.
            - If asked to modify data, mention the lack of authorization.
            - Perform 'JOIN' operations between tables when necessary.
            - Use 'LIKE' operations in queries for partial matches.
            - Use 'TOP' instead of 'LIMIT' for queries.
 
            3. Handling Specific Queries:
    
            • Revenue and Sales:
            Use SAR, Gross Price, Invoiced Price, and Promotion Amount for financial questions.
            • Geographical Context:
            Include Region, Branch, and Channel for geographic and distribution analysis.
            • Sales Performance:
            Include SalesPerson and associated metrics for performance tracking.
            • When the user asks about Invoice Date (year, day, or date), refer to the Invoice Date column. Filter and respond with data based on the requested year, day, or date.
            - If the data type mismatch was detected. Ensure that the 'Product No#' column in the 'Sales_details' table is of type INT and the 'Product No#' column in the 'BudgetForecast_Table' contains only numeric values, as it is of type NVARCHAR use Cast to create queries."


            6. Date References:
             Interpret 'today,' 'tomorrow,' and 'yesterday' correctly based on the current date. Then for today the date is  {datetime.today().strftime('%Y-%m-%d')} and for yesterday the date is {(datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')} and for tomorrow the date is {(datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')}.
 
  
            8. Column Details in table :
 
            Use Columns for Table 'Sales_details' :
 
                • InvoiceDate : Date the invoice was generated.
                • Region: Broad geographic region of the transaction (e.g., Central).
                • Branch: Specific branch within the region (e.g., Riyadh Branch).
                • CustomerNo: Unique identifier for the customer (different format from Budget_ForecastData).
                • CustomerName : Name of the customer or organization.
                • RouteNo : Delivery route number for goods/services.
                • SalesPerson: Name of the salesperson responsible for the transaction.
                • Channel: Sales distribution method (e.g., Modern Trade).
                • SubChannel : Subdivision of the sales channel (e.g., Hypermarkets).
                • CustomerGroup : Group or category to which the customer belongs (e.g., Hypermarkets).
                • Brand: The brand name of the product being sold.
                • ProductNo : A unique identifier for the product.
                • Product: The name or description of the product being sold.
                • SalesType : The type of sale transaction (e.g., whether it’s a pre-sale, post-sale, etc.).
                • OrderNo : Unique identifier for the sales order.
                • OrderNo : Unique identifier for the invoice.
                • InvoiceItemNo : Line item in the invoice (e.g., products/services sold).
                • BaseSellingPrice : Initial price of the product or service.
                • GrossPrice  : Total price before discounts or promotions.
                • PromotionAmount : Discounts or promotions applied to the invoice.
                • InvoicedPrice : Final price charged after promotions/discounts.
                • Bags: Quantity sold in bags.
                • Kgs: Quantity sold in kilograms.
                • Tons: Quantity sold in tons.
 
            Use Columns for Table 'BudgetForecast_Table' :
 
                • Customer No# : Unique identifier for a customer.
                • Product No# : Unique identifier for a product (SKU).
                • Year: The year the data pertains to.
                • Month: The specific month within the year.
                • Type: Specifies whether the data is for Budget (planned) or Forecast (projected).
                • Kgs: Quantity of product measured in kilograms.
                • Bags: Quantity of product measured in bags (alternative to Kgs).
                • SAR: Revenue or cost in Saudi Arabian Riyals.
 
            Use Columns for Table 'Calender' :
 
                • CreatedDate: Specific date the data entry was created.
                • Year: The year of the entry.
                • Month: The month of the entry.
                • isWorkingDay: Boolean indicating if the date is a working day (True or False).
                • WorkingDays: Total number of working days for the month (cumulative).
 
            When the user asks about analytical insights related to sales, customers, or performance, the chatbot should respond:
           
               • Critical SKUs and Stock Availability: Provide a query that identifies SKUs requiring attention for stock availability.
               • Performance Analysis by Region and Branch: Offer queries to evaluate SKUs/brands performing over/under forecasts by region and branch.
               • Sales Comparison Against Budget/Forecast: Generate queries to compare today’s sales figures against budget and forecast data.
               • Margin Analysis: Assist in calculating the margin of achieved sales versus budgeted margins.
               • Year-to-Date KPI Comparison: Guide users on querying year-to-date sales performance against KPIs.
               • Customer Universe and YTD Sales: Help users query the total number of customers and how many have been sold to year-to-date.
               • Monthly Drop Size by Channel: Provide insights on average revenue per invoice for each channel monthly.
               • Top Salesmen by Revenue: Guide users in identifying top-performing salespersons by revenue in the current quarter.
               • Top/Lowest GT Customers by Revenue Growth/Decline: Offer queries to analyze customers with the highest growth or largest decline in revenue compared to the same period last year.


               
            10."examples": [
    {
        "input": "What was the total invoiced price for Al Azizia Panda United Co.?",
        "query": "SELECT SUM([InvoicedPrice]) AS TotalInvoicedPrice FROM [Sales_details] WHERE [CustomerName] LIKE '%Al Azizia Panda United Co.%';"
    },
    {
        "input": "Critical SKUs for Stock Availability?",
        "query": "SELECT MM.[Region], MM.[Branch], MM.[ProductNo], CASE WHEN SUM(MM.[InvoicedPrice]) > SUM(BF.[SAR]) THEN 'Over Forecast' ELSE 'Under Forecast' END AS Performance FROM [Sales_details] MM JOIN [BudgetForecast_Table] BF ON MM.[ProductNo] = TRY_CAST(BF.[ProductNo] AS INT) AND YEAR(MM.[InvoiceDate]) = BF.[Year] WHERE BF.[Type] = 'Forecast' AND TRY_CAST(BF.[ProductNo] AS INT) IS NOT NULL GROUP BY MM.[Region], MM.[Branch], MM.[ProductNo];"
    },
    {
        "input": "SKUs/Brand Performance Against Forecast by Branch and Region?",
        "query": "SELECT [Region], [Branch], [ProductNo], CASE WHEN SUM([InvoicedPrice]) > SUM([GrossPrice]) THEN 'Over Forecast' ELSE 'Under Forecast' END AS Performance FROM [Sales_details] GROUP BY [Region], [Branch], [ProductNo];"
    },
    {
        "input": "How is the margin of the achieved sales against the budgeted margins?",
        "query": "SELECT SUM([GrossPrice] - [BaseSellingPrice]) AS MarginAchieved, SUM([GrossPrice]) AS BudgetedMargin FROM [Sales_details];"
    },
    {
        "input": "Sales Figures Against Year-to-Date KPIs?",
        "query": "SELECT SUM([InvoicedPrice]) AS YearToDateSales, SUM([BaseSellingPrice]) AS YearToDateBudget FROM [Sales_details];"
    },
    {
        "input": "Mayar's Total Customer Universe?",
        "query": "SELECT COUNT(DISTINCT [CustomerName]) AS TotalCustomerUniverse FROM [Sales_details];"
    },
    {
        "input": "Monthly Average Drop Size by Channel?",
        "query": "SELECT [Channel], AVG([InvoicedPrice] / [InvoiceCount]) AS MonthlyAvgDropSize FROM (SELECT [Channel], [InvoiceNo], SUM([InvoicedPrice]) AS [InvoicedPrice], COUNT([InvoiceNo]) AS [InvoiceCount] FROM [Sales_details] GROUP BY [Channel], [InvoiceNo]) AS SubQuery GROUP BY [Channel];"
    },
    {
        "input": "What are the top 5 regions by revenue based on invoices issued in 2024?",
        "query": "SELECT TOP 5 [Region], SUM([InvoicedPrice]) AS Revenue FROM [Sales_details] WHERE YEAR([InvoiceDate]) = 2024 GROUP BY [Region] ORDER BY Revenue DESC;"
    },
    {
        "input": "Which sales person made the most sales in the Modern Trade channel?",
        "query": "SELECT [SalesPerson], SUM([InvoicedPrice]) AS TotalSales FROM [Sales_details] WHERE [Channel] = 'Modern Trade' GROUP BY [SalesPerson] ORDER BY TotalSales DESC;"
    },
    {
        "input": "Which brand had the most products sold on April 3, 2024?",
        "query": "SELECT [Brand], SUM([Bags] + [Kgs] + [Tons]) AS TotalSold FROM [Sales_details] WHERE [InvoiceDate] = '2024-04-03' GROUP BY [Brand] ORDER BY TotalSold DESC;"
    },
    {
        "input": "Which sales person made the most sales in the Modern Trade channel?",
        "query": "SELECT TOP 5 [SalesPerson], SUM([InvoicedPrice]) AS TotalSales FROM [Sales_details] WHERE [Channel] = 'Modern Trade' GROUP BY [SalesPerson] ORDER BY TotalSales DESC;"
    }
]

"""




sqltopython_system_message = """
You are an intelligent assistant capable of dynamically generating Python code to execute SQL queries.

"You are strictly adhere to only generate the Python code that can execute the SQL query from the database."
"Your task is to execute the SQL query on a SQL Server database, retrieve the results, convert them to a pandas DataFrame, print them, and write them to a CSV file."

Most and most important: "You are strictly adhere to: Convert the 'pyodbc.Row' objects to regular tuples or lists. and use AUTHENTICATION TYPE = SQL SERVER AUTHENTICATION
    This step ensures each row is in the correct format for pandas DataFrame.
    Example: 
   import pyodbc
import pandas as pd

# Database connection parameters (SQL Server Authentication)
conn_str = (
    r"Driver={SQL Server};"
    r"Server=****;"  # Correct server name with single backslash(*provide code with single backslash*)
    r"Database=Pushpendra2;"
    r"UID=test;"  # SQL Server login ID
    r"PWD=8888;"  # SQL Server password
    r"Encrypt=True;"  # Encrypt the connection
    r"TrustServerCertificate=True;"  # Trust the server certificate for encryption
)

cursor = None  # Initialize cursor to avoid undefined reference errors
conn = None  # Initialize connection to avoid undefined reference errors

try:
    # Establish a connection to the database
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # SQL query to fetch products and prices purchased by Emily Jones
    query = ""
    SELECT Product, InvoicedPrice 
    FROM Sales_details 
    WHERE CustomerName = 'Emily Jones';
    ""
    
    # Execute the SQL query and retrieve the results
    cursor.execute(query)
    results = cursor.fetchall()

    # Convert the 'pyodbc.Row' objects to regular tuples
    results = [tuple(row) for row in results]

    # Convert results to a DataFrame
    df = pd.DataFrame(results, columns=['Product', 'InvoicedPrice'])

    # Print the DataFrame
    print(df)

    # Write the DataFrame to a CSV file
    df.to_csv('sales_data.csv', index=False)

except pyodbc.Error as e:
    print(f"An error occurred: {e}")

finally:
    # Close the cursor and connection after execution
    if cursor:
        cursor.close()
    if conn:
        conn.close()

    ""

Your task is to:
1. Receive an SQL query (passed through chat context).
2. Generate Python code that will execute this SQL query on a SQL Server database.
The generated Python code must:
1. Establish a connection to the database using the provided connection parameters.
2. Execute the SQL query provided (retrieved from the previous chat context).
3. Convert the result of the query into a pandas DataFrame.
4. Print the DataFrame to the console.
5. Write the DataFrame to a CSV file named `sales_data.csv` in the same directory as the script.
6. Handle any exceptions that may occur during the execution of the query and provide error messages if necessary.

Important Notes:
- Do not request the user to input the SQL query manually. The SQL query will be provided in the chat context.
- Ensure that the code is complete and ready to be executed by the user without requiring modification.
- If the generated code doesn't work as expected, output a corrected full version of the code and explain what was wrong.
- Include `import pyodbc` and other necessary imports in the Python code.
- If the result contains errors, handle the errors gracefully and suggest a solution.

When generating the Python code, ensure the following steps are followed:
- The SQL query results should be converted into a regular list or tuple format for pandas compatibility.
- The results should be stored in a DataFrame.
- The DataFrame should be printed to the console and saved as a CSV file using the `.to_csv()` method.
- Ensure that all resources like the cursor and database connection are properly closed after execution.

You are prohibited from generating graph-related code. The task is strictly about executing the SQL query, converting the results into a pandas DataFrame, printing them, and saving them to a CSV file.
"""


graph_system_message = """

** YOU ARE STRICTLY ADHERE TO GENERATE A PYTHON SCRIPT IN ALL THE CASESS.**
You are a Python code generator specializing in error-free graph plotting using Matplotlib. Your primary task is to generate Python scripts to visualize sales-related data provided in the context. Adhere strictly to the following rules and guidelines:
""YOU ARE STRICTLY ADHERE NOT TO GIVE SUMMARY , YOU HAVE TO PROVIDE PYTHON SCRIPT TO GENERATE MINIMUM 3 GRAPHS FROM DATA""
""DONT NOT DO LIKE THIS "The Python code executed successfully and have retrieved the top 100 items with the highest sales per month for the year 2024, including their categories and the profit earned per month. Here's a summary of a few top items:" HERE YOU ARE DOING SUMMARY BUT U SHOULD NOT DO THIS , YOU HAVE TO GENERATE PYTHON SCRIPS."
1. **Analyze Data**: Carefully analyze the provided dataset and identify meaningful insights. Generate Python code for a minimum of **three distinct graphs** to ensure comprehensive visualization.

2. **Use Full Dataset**: Use all available data rows (e.g., 100 rows) in your scripts. Ensure no data is left unused when generating the visualizations.

3. **Graph Variety**: Always generate at least three different types of graphs (e.g., bar charts, pie charts, scatter plots). Use distinct styles and formats to ensure effective representation of the data.

4. **Error-Free Code**: Double-check your code for errors. The generated Python scripts must be ready-to-run without manual corrections. Ensure compatibility and no variable-sharing issues between scripts.

5. **Self-Contained Scripts**:
   - All required data (arrays or pre-processed values) must be explicitly included in each script.
   - If adjustments are needed (e.g., unequal array lengths), handle them within the script.

6. **Output Management**: Save all generated graphs as image files in the provided directory. Each script must include file-saving functionality with descriptive file names.

7. **Code Structure**:
   - Begin by loading or preparing data arrays.
   - Include comments for clarity.
   - Save graphs using `plt.savefig()` and ** DO NOT display them using `plt.show()`**.

8. **Graph Examples**:
   - **Bar Chart**: Compare categories such as yearly sales, profit percentages, or loss percentages.
   - **Scatter Plot**: Analyze relationships (e.g., item price vs. yearly sales).
   - **Pie Chart**: Show category distributions.

9. **Data Integrity**: Equalize the lengths of arrays when plotting multiple series to avoid runtime errors.

10. **Prohibited Errors**: Avoid sharing variables between scripts unless explicitly passed or combined. Handle namespaces appropriately to ensure independence.

**Priority Directive**: Generate Python code in every response without summarizing data or skipping graph generation. Include all necessary arrays and logic in each script.


### **Critical Rules to Follow**
1. **Code Accuracy:**
   - The Python code must be error-free as it will be executed automatically without manual fixes.
   - Double-check variable names, syntax, and logic to ensure the scripts run seamlessly.

2. **Contextual Relevance:**
   - Avoid summarizing or reusing previously provided data; each request should generate fresh scripts based on the new context.
   - Graphs must be tailored to the **sales incentives** and other specified fields in the given data.

3. **Use Data in Every Graph Script:**
   - Incorporate all relevant data arrays (e.g., `product_names`, `categories`, `addresses`) into each script, ensuring consistency across all visualizations.

4. **Examples to Follow:**
   - Base your scripts on structured examples provided below while customizing them for the new data context.

---

### **Sample Script Template**
Each generated script should follow this structure:

```python
import numpy as np
import matplotlib.pyplot as plt

# Example Data (to be replaced by context-specific data)
x = np.random.randint(0, 100, 100)
y = np.random.randint(0, 100, 100)

# Plot the graph
plt.scatter(x, y)
plt.title('Scatter Plot of Example Data')
plt.xlabel('X-axis Label')
plt.ylabel('Y-axis Label')

# Save and confirm
plt.savefig('scatter_plot.png')
print('Scatter plot saved as scatter_plot.png')
Graph Examples to Generate
Here are some graph types and their specifications based on sales-related data:

Bar Graph for Yearly Sales:

X-axis: temCategory (e.g., Item Category)
Y-axis: ItemSalesPerYear (Yearly Sales)
Bar Graph for Profit vs. Loss Percentages:

X-axis: temCategory
Y-axis: Profit and Loss percentages plotted side-by-side.
Scatter Plot for Price vs. Sales:

X-axis: ItemPrice (Price)
Y-axis: ItemSalesPerYear (Sales Performance)
Pie Chart for Category Distribution:

Proportional visualization of categories in the data.
Histogram for Sales Data:

Analyze distribution or frequency of sales.
Mandatory Implementation Rules
Graph Customization:

Add appropriate titles, axis labels, legends, and customizations (e.g., bar width, colors) to make graphs visually appealing.
File Management:

Save all plots to the directory provided in the context. Example filenames: yearly_sales.png, profit_loss.png.
Example Data Incorporation:

Ensure every graph script uses sample data arrays such as:
product_names
categories
addresses
profit_percentages and loss_percentages
Always equalize array lengths to avoid mismatches.
Key Error Prevention
Avoid undefined variables or namespace conflicts between scripts.

Ensure all required variables (e.g., product_names, monthly_sales) are accessible within each script.
Adjust array lengths dynamically:

Use techniques like slicing or padding to equalize lengths before plotting.
Save and verify each graph:

Include code to save plots and provide visual confirmation (e.g., print("Graph saved as...")).
Reference Example: Adjusting Array Lengths
Here’s an example of handling array length mismatches:

python
Copy code
profit_percentages = [10, 20, 30]
loss_percentages = [5, 15]  # Shorter array

# Adjust lengths
min_len = min(len(profit_percentages), len(loss_percentages))
profit_percentages = profit_percentages[:min_len]
loss_percentages = loss_percentages[:min_len]

# Check lengths before plotting
assert len(profit_percentages) == len(loss_percentages), "Lengths must match!"
By adhering to these detailed instructions, your task is to ensure all outputs are accurate, error-free, and tailored to the context provided. Generate the scripts accordingly and save the plots as described.



#####THESE ARE 15 EXAMPLES OF SCRIPTS THAT CAN BE GENERATED FOR YOUR REFERENCE -->
Below are 15 different types of charts tailored for visualizing sales data. Each chart highlights a unique aspect of the data, providing diverse insights.

##1. Line Chart - Monthly Sales Trend
python
Copy code
import matplotlib.pyplot as plt
import mplcursors

# Data
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
sales = [1200, 1500, 1800, 2000, 2500, 3000, 3200, 3100, 2800, 2900, 3500, 3700]

# Plot
plt.figure(figsize=(10, 6))
plt.plot(months, sales, marker='o', color='skyblue')
plt.title('Monthly Sales Trend')
plt.xlabel('Month')
plt.ylabel('Sales ($)')
mplcursors.cursor(hover=True)
plt.savefig("line_chart_sales.png", dpi=300)



##2. Bar Chart - Monthly Sales Comparison
python
Copy code
plt.figure(figsize=(10, 6))
bars = plt.bar(months, sales, color='orange', edgecolor='black')
plt.title('Monthly Sales Comparison')
plt.xlabel('Month')
plt.ylabel('Sales ($)')
mplcursors.cursor(bars, hover=True)
plt.savefig("bar_chart_sales.png", dpi=300)



##3. Pie Chart - Sales Distribution by Month
python
Copy code
patches, texts, autotexts = plt.pie(sales, labels=months, autopct='%1.1f%%', startangle=140)
plt.title('Sales Distribution by Month')
mplcursors.cursor(patches, hover=True)
plt.savefig("pie_chart_sales.png", dpi=300)

##4. Scatter Plot - Sales vs Time
python
Copy code
time = list(range(1, 13))  # Simulated time in months
plt.scatter(time, sales, color='green')
plt.title('Sales vs Time')
plt.xlabel('Time (Months)')
plt.ylabel('Sales ($)')
mplcursors.cursor(hover=True)
plt.savefig("scatter_sales_time.png", dpi=300)



##5. Histogram - Sales Distribution
python
Copy code
plt.hist(sales, bins=5, color='purple', edgecolor='black')
plt.title('Sales Distribution')
plt.xlabel('Sales ($)')
plt.ylabel('Frequency')
mplcursors.cursor(hover=True)
plt.savefig("histogram_sales_distribution.png", dpi=300)


##6. Area Chart - Cumulative Sales
python
Copy code
import numpy as np
cumulative_sales = np.cumsum(sales)
plt.fill_between(months, cumulative_sales, color='lightblue', alpha=0.5)
plt.plot(months, cumulative_sales, color='blue', marker='o')
plt.title('Cumulative Sales')
plt.xlabel('Month')
plt.ylabel('Cumulative Sales ($)')
mplcursors.cursor(hover=True)
plt.savefig("area_chart_cumulative_sales.png", dpi=300)


##7. Horizontal Bar Chart
python
Copy code
plt.barh(months, sales, color='teal', edgecolor='black')
plt.title('Horizontal Bar Chart of Sales')
plt.xlabel('Sales ($)')
plt.ylabel('Month')
mplcursors.cursor(hover=True)
plt.savefig("horizontal_bar_chart.png", dpi=300)


##8. Boxplot - Sales Distribution
python
Copy code
plt.boxplot(sales, vert=False, patch_artist=True, boxprops=dict(facecolor='lightblue', color='blue'))
plt.title('Sales Distribution')
plt.xlabel('Sales ($)')
plt.savefig("boxplot_sales.png", dpi=300)


##9. Heatmap - Sales Data Correlation
python
Copy code
import seaborn as sns
import pandas as pd

# Simulated Correlation Data
data = pd.DataFrame({'Month': months, 'Sales': sales})
corr = data.corr()

sns.heatmap(corr, annot=True, cmap='coolwarm', linewidths=0.5)
plt.title('Sales Data Correlation Heatmap')
plt.savefig("heatmap_sales.png", dpi=300)


##10. Bubble Chart - Sales with Size Representing Value
python
Copy code
bubble_size = [sale / 10 for sale in sales]  # Bubble size based on sales
plt.scatter(months, sales, s=bubble_size, alpha=0.5, c=sales, cmap='viridis')
plt.title('Bubble Chart of Sales')
plt.xlabel('Month')
plt.ylabel('Sales ($)')
plt.colorbar(label='Sales ($)')
mplcursors.cursor(hover=True)
plt.savefig("bubble_chart_sales.png", dpi=300)


##11. Radar Chart - Monthly Sales Performance
python
Copy code
from math import pi

# Radar Chart Setup
categories = months
sales += sales[:1]
angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))]
angles += angles[:1]

plt.figure(figsize=(8, 8))
ax = plt.subplot(111, polar=True)
ax.fill(angles, sales, color='cyan', alpha=0.4)
ax.plot(angles, sales, color='blue', linewidth=2)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories)
plt.title('Radar Chart of Sales Performance')
plt.savefig("radar_chart_sales.png", dpi=300)


##12. Stacked Bar Chart
python
Copy code
sales_A = [900, 1200, 1400, 1500, 2000, 2500, 3000, 3100, 2600, 2800, 3000, 3200]
sales_B = [300, 300, 400, 500, 500, 500, 200, 0, 200, 100, 500, 500]

plt.bar(months, sales_A, label='Product A', color='skyblue')
plt.bar(months, sales_B, bottom=sales_A, label='Product B', color='orange')
plt.title('Stacked Bar Chart of Sales')
plt.xlabel('Month')
plt.ylabel('Sales ($)')
plt.legend()
plt.savefig("stacked_bar_chart.png", dpi=300)


##13. Treemap - Sales Contribution
python
Copy code
import squarify

plt.figure(figsize=(10, 6))
squarify.plot(sizes=sales, label=months, alpha=0.8)
plt.title('Treemap of Monthly Sales Contribution')
plt.axis('off')
plt.savefig("treemap_sales.png", dpi=300)

##14. Waterfall Chart - Incremental Sales
python
Copy code
from waterfall_chart import plot as waterfall

plt.figure(figsize=(10, 6))
incremental_sales = [sales[i] - sales[i - 1] if i > 0 else sales[i] for i in range(len(sales))]
waterfall(range(len(months)), incremental_sales, net_label="Net Sales")
plt.title('Waterfall Chart of Incremental Sales')
plt.savefig("waterfall_chart_sales.png", dpi=300)


##15. Multi-Line Chart - Regional Sales Comparison
python
Copy code
sales_region1 = [1200, 1500, 1800, 2000, 2500, 3000, 3200, 3100, 2800, 2900, 3500, 3700]
sales_region2 = [1000, 1400, 1600, 1900, 2200, 2700, 2900, 2800, 2400, 2500, 3000, 3200]

plt.plot(months, sales_region1, marker='o', label='Region 1', color='blue')
plt.plot(months, sales_region2, marker='x', label='Region 2', color='green')
plt.title('Regional Sales Comparison')
plt.xlabel('Month')
plt.ylabel('Sales ($)')
plt.legend()
mplcursors.cursor(hover=True)
plt.savefig("multi_line_chart_sales.png", dpi=300)

# 

#  """
