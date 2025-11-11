import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import requests
import re
import os
from dotenv import load_dotenv

# --- Load API key ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash-lite"
BASE_URL = f"https://generativelanguage.googleapis.com/v1/models/{MODEL}:generateContent?key={API_KEY}"

st.set_page_config(page_title="Olist GenAI Data Agent", layout="wide")
st.title("Olist GenAI Data Agent")
st.caption("Conversational Data Assistant powered by Gemini + DuckDB")

# --- Load and cache data ---
@st.cache_data
def load_data():
    base = "data/"
    orders = pd.read_csv(base + "olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp"])
    items = pd.read_csv(base + "olist_order_items_dataset.csv")
    products = pd.read_csv(base + "olist_products_dataset.csv")
    payments = pd.read_csv(base + "olist_order_payments_dataset.csv")
    customers = pd.read_csv(base + "olist_customers_dataset.csv")

    df = (orders.merge(items, on="order_id", how="left")
                .merge(products, on="product_id", how="left")
                .merge(payments, on="order_id", how="left")
                .merge(customers, on="customer_id", how="left"))
    return df

df = load_data()
max_date = df["order_purchase_timestamp"].max()
st.info(f"Data covers up to: {max_date.date()}")
con = duckdb.connect(database=':memory:')
con.register("olist", df)
st.success("Data loaded successfully into DuckDB")

# --- Helper functions ---
def clean_sql(sql_text):
    """Remove markdown fences and backticks safely."""
    if sql_text is None:
        return ""
    sql_text = re.sub(r"```[a-zA-Z]*", "", sql_text)
    sql_text = sql_text.replace("```", "")
    return sql_text.strip(" \n\r`")

def gemini_call(prompt):
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    response = requests.post(BASE_URL, headers=headers, json=payload)
    return response.json()

def generate_sql(user_query, history_text=""):
    schema = "['order_id','order_status','order_purchase_timestamp','price','freight_value','product_id','product_category_name','payment_type','payment_value','customer_id','customer_state','seller_id']"
    prompt = f"""
You are a data analyst writing SQL for DuckDB (PostgreSQL-like syntax).
Use CURRENT_DATE and INTERVAL for date arithmetic (e.g., CURRENT_DATE - INTERVAL 6 MONTH).
Do not use STRFTIME or DATE('now').
Work on a table called olist with columns {schema}.
User conversation so far:
{history_text}
Now write only the SQL query (no explanations) to answer:
User: {user_query}
SQL:
"""
    res = gemini_call(prompt)
    try:
        sql = res["candidates"][0]["content"]["parts"][0]["text"]
        sql = clean_sql(sql)
        return sql
    except Exception:
        st.error("Gemini could not generate SQL.")
        st.write(res)
        return None

def explain_results(df, user_query):
    csv = df.head(10).to_csv(index=False)
    prompt = f"Summarize these results in 2–3 short business insights for the question: {user_query}\n\n{csv}"
    res = gemini_call(prompt)
    try:
        return res["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return "Could not generate summary."

def fix_sql(original_sql, error_message):
    fix_prompt = f"""The following SQL query failed in DuckDB:
{original_sql}
Error: {error_message}
Please correct it. Use CURRENT_DATE and INTERVAL syntax where necessary.
Only return valid SQL.
"""
    res = gemini_call(fix_prompt)
    try:
        fixed_sql = res["candidates"][0]["content"]["parts"][0]["text"]
        fixed_sql = clean_sql(fixed_sql)
        # Replace CURRENT_DATE with dataset max date here too
        fixed_sql = fixed_sql.replace("CURRENT_DATE", f"DATE '{max_date.date()}'")
        return fixed_sql
    except Exception:
        return None


# --- Conversation memory ---
if "history" not in st.session_state:
    st.session_state.history = []

user_query = st.text_input("Ask your data question (e.g., 'Top 5 product categories by sales last year'):")
run_btn = st.button("Run Analysis")

if run_btn and user_query:
    st.session_state.history.append({"user": user_query})
    history_text = "\n".join([f"User: {h['user']}" for h in st.session_state.history[:-1]])

    with st.spinner("Generating SQL..."):
        sql_query = generate_sql(user_query, history_text)

    if sql_query:
        st.subheader("Generated SQL")
        st.code(sql_query, language="sql")

        #Translate English → Portuguese category names before execution
        category_map = {
            "electronics": "eletronicos",
            "furniture": "moveis_decoracao",
            "fashion": "fashion_bolsas_e_acessorios",
            "health_beauty": "beleza_saude",
            "toys": "brinquedos",
            "books": "livros_tecnicos",
        }
        for eng, por in category_map.items():
            sql_query = sql_query.replace(f"'{eng}'", f"'{por}'")

        try:
            #Replace CURRENT_DATE with dataset’s max date
            sql_query = sql_query.replace("CURRENT_DATE", f"DATE '{max_date.date()}'")
            result = con.execute(sql_query).df()
        except Exception as e:
            st.warning(f"SQL failed: {e}")
            with st.spinner("Auto-correcting SQL..."):
                fixed_sql = fix_sql(sql_query, str(e))
                if fixed_sql:
                    st.code(fixed_sql, language="sql")
                    try:
                        result = con.execute(fixed_sql).df()
                    except Exception as e2:
                        st.error(f"Still invalid after correction: {e2}")
                        result = pd.DataFrame()
                else:
                    result = pd.DataFrame()

        if not result.empty:
            st.dataframe(result.head(20))

            # Auto chart
            num_cols = result.select_dtypes(include="number").columns
            if len(num_cols) >= 1:
                x = result.columns[0]
                y = num_cols[0]
                fig = px.bar(result, x=x, y=y, title="Visualization")
                st.plotly_chart(fig, use_container_width=True)

            with st.spinner("Summarizing insights..."):
                summary = explain_results(result, user_query)
                st.write("**Insight Summary:**")
                st.write(summary)
                st.session_state.history[-1]["summary"] = summary
        else:
            st.warning("No data returned for this query.")
    else:
        st.warning("Gemini could not generate SQL for that query.")


# --- Sidebar conversation history ---
st.sidebar.header("Conversation History")
for h in st.session_state.history:
    st.sidebar.write(f"{h['user']}")
    if "summary" in h:
        st.sidebar.caption(h["summary"])
