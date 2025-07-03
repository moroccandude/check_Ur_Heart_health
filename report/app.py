import streamlit as st
import pandas as pd
from pyhive import hive
from datetime import datetime

# --- Page Config ---
st.set_page_config(
    page_title="Heart Disease Analytics Platform",
    page_icon="🫀",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
  .main-header { font-size: 2.75rem; color: #e63946; text-align: center; margin: 2rem 0; }
  .metric-card { background: #ffffff; border-radius: 1rem; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
  .metric-value { font-size: 2.25rem; font-weight: 700; color: #2b2d42; }
  .metric-label { font-size: 1rem; color: #8d99ae; }
  .filter-container { padding: 1rem; background: #f8f9fa; border-radius: 0.75rem; }
  .welcome-header { 
        font-size: 3rem; 
        color: #1a237e; 
        text-align: center; 
        margin: 2rem 0; 
    }
    .welcome-subheader { 
        font-size: 1.5rem; 
        color: #455a64; 
        text-align: center; 
        margin-bottom: 2rem; 
    }
</style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 class='main-header'>Welcome to Heart Disease Analytics Platform</h1>", unsafe_allow_html=True)
st.markdown("<p class='welcome-subheader'>Comprehensive Data Management & Analytics Solution</p>", unsafe_allow_html=True)

# Quick links
col1, col2, col3 = st.columns(3)
with col1:
    st.info("📊 [Go to Dashboard](/dashboard)")
with col2:
    st.info("🏛️ [Data Governance](/governance)")
with col3:
    st.info("📝 [Documentation](https://docs.example.com)")

# --- Hive Connection ---
@st.cache_resource(show_spinner=False)
def get_hive_conn():
    try:
        return hive.Connection(host="hiveserver2", port=10000,
                               username="hive", password="password",
                               database="default", auth='CUSTOM')
    except Exception as e:
        st.error(f"Unable to connect to Hive: {e}")
        return None

# --- Query Executor ---
@st.cache_data(show_spinner=False, ttl=300)
def fetch_query(query: str) -> pd.DataFrame:
    conn = get_hive_conn()
    if not conn:
        return pd.DataFrame()
    with st.spinner("Loading data..."):
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
        return pd.DataFrame(rows, columns=cols)

# --- Sidebar Filters ---
st.sidebar.header("Filters & Database Explorer")
# Test Connection
def test_conn():
    df = fetch_query("SHOW TABLES")
    if not df.empty:
        st.sidebar.success(f"Connected, {len(df)} tables found")
    else:
        st.sidebar.error("Connection failed or no tables found.")
if st.sidebar.button("Test Hive Connection"): test_conn()

# Table Selector
tables = fetch_query("SHOW TABLES").iloc[:,0].tolist()
selected_table = st.sidebar.selectbox("Select Table", tables) if tables else None

# Gender Filter
st.sidebar.markdown("---")
gender_opts = {"Male": 1, "Female": 0}
selected_gender = st.sidebar.radio("Gender", list(gender_opts.keys()), index=0)
sex_value = gender_opts[selected_gender]

# Age Filter
age_min, age_max = st.sidebar.slider("Age Range", 29, 77, (29, 77))

# --- Main Content ---
if selected_table:
    # Dynamic Query
    base_query = f"SELECT * FROM {selected_table} WHERE sex = {sex_value} " \
                 f"AND age BETWEEN {age_min} AND {age_max}"
    if selected_table == "coronary_artery_disease":
            get_total_targets= f"SELECT COUNT(target) AS total FROM {selected_table} " 
            targets_df= fetch_query(get_total_targets)
            st.markdown(f"<h5>Total patiences</h5> = {int(targets_df['total'][0])}", unsafe_allow_html=True)
    df_data = fetch_query(base_query + " LIMIT 1000")
    st.markdown(f"<h5>geneder</h5> = {sex_value}", unsafe_allow_html=True)
    st.markdown(f"<h3>Showing top 1,000 records for <em><b>{selected_table}</bm></em></h3>", unsafe_allow_html=True)
    st.dataframe(df_data, use_container_width=True)

    # Metrics Row
    col1, col2, col3 = st.columns(3, gap='large')
    with col1:
        total = fetch_query(base_query.replace("*", "COUNT(*) AS total_cases"))
        val = int(total['total_cases'][0]) if not total.empty else 0
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Total Cases</div>"
                    f"<div class='metric-value'>{val}</div></div>", unsafe_allow_html=True)
    with col2:
        disease = fetch_query(base_query.replace("*", "COUNT(*) AS diseased").replace("WHERE", "WHERE target=1 AND"))
        val2 = int(disease['diseased'][0]) if not disease.empty else 0
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Heart Disease</div>"
                    f"<div class='metric-value'>{val2}</div></div>", unsafe_allow_html=True)
    with col3:
        healthy = fetch_query(base_query.replace("*", "COUNT(*) AS healthy").replace("WHERE", "WHERE target=0 AND"))
        val3 = int(healthy['healthy'][0]) if not healthy.empty else 0
        st.markdown(f"<div class='metric-card'><div class='metric-label'>No Disease</div>"
                    f"<div class='metric-value'>{val3}</div></div>", unsafe_allow_html=True)

    # Fast Insights
    st.markdown("---")
    insight_query = (f"SELECT cp, COUNT(*) AS count FROM {selected_table} "
                     f"WHERE sex={sex_value} AND age BETWEEN {age_min} AND {age_max} "
                     f"GROUP BY cp ORDER BY count DESC LIMIT 5")
    insights = fetch_query(insight_query)
    if not insights.empty:
        st.bar_chart(insights.set_index('cp')['count'])
    else:
        st.info("No insight data to display.")
else:
    st.info("Please select a table from the sidebar to begin.")
