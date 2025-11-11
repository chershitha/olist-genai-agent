# olist-genai-agen
Olist GenAI Data Agent:
A conversational AI-powered data analytics assistant built using **Google Gemini**, **Streamlit**, and **DuckDB**, designed to analyze the Olist Brazilian E-Commerce dataset using natural language queries.

Problem Statement:
Data analysis often requires technical SQL skills.  
This project solves that by allowing anyone to interact with an e-commerce dataset using plain English questions.  
The system translates natural queries into SQL, executes them on DuckDB, and presents both data visualizations and human-friendly insights.

Overview:
The Olist GenAI Data Agent:
- Takes natural language questions
- Converts them into SQL queries via Google Gemini
- Executes them on DuckDB
- Displays dataframes + charts
- Generates summaries of insights
- Auto-corrects invalid SQL
- Handles time and category translations
- Maintains conversation history

System Architecture:
(docs/architecture.png)

Component Flow:

Component | Function 
User Interface (Streamlit) | Users input natural queries via a chat-like interface.
Gemini API (LLM Brain) | Converts user text to SQL, explains results, and fixes SQL errors.
Backend Logic (Streamlit) | Executes queries, adjusts dates, maps category names, displays results. 
DuckDB Database | Stores the Olist dataset in-memory for fast analytics. 

 Tech Stack:
 Layer | Technology Used 
Frontend/UI | Streamlit 
Language Model | Google Gemini (`gemini-2.0-flash-lite`) 
Database | DuckDB (in-memory SQL) 
Visualization | Plotly 
Language | Python 3.10+ 
Data Source | [Olist Brazilian E-Commerce Dataset (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/) 

Clone this repository:
git clone https://github.com/your-username/olist-genai-agent.git
cd olist-genai-agent

Installation & Setup:
Install dependencies-
pip install -r requirements.txt
In the .env file replace the gemini api key with your api key
Download the dataset from Kaggle – Brazilian E-Commerce by Olist and place all CSV files inside the /data directory
Run the application: streamlit run app.py


