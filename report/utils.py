import streamlit as st
from pyhive import hive
import pandas as pd

@st.cache_resource
def get_hive_connection():
    return hive.Connection(
        host="hiveserver2",
        port=10000,
        username="hive",
        password="password",
        database="default",
        auth='CUSTOM'
    )

@st.cache_data(ttl=300)
def fetch_query(query: str) -> pd.DataFrame:
    conn = get_hive_connection()
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
    return pd.DataFrame(rows, columns=cols)