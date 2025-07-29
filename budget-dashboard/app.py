import streamlit as st
import pandas as pd
import plotly.express as px

# --- Load & preprocess ---
@st.cache_data
def load_data():
    df = pd.read_csv("test_transactions.csv")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=["Date"])
    df["Month"] = df["Date"].dt.to_period("M")
    return df

df = load_data()

# Budget calculation
monthly = df.groupby(["Month", "Category"])["Amount"].sum().reset_index()
budget = monthly.groupby("Category")["Amount"].mean().apply(lambda x: round(x * 0.8, 2)).reset_index(name="Budget")

# --- Sidebar Filters ---
st.sidebar.header("🔧 Filters")
category = st.sidebar.selectbox("Select Category", sorted(df["Category"].unique()))
months_sorted = sorted(df["Month"].astype(str).unique())
month_range = st.sidebar.slider(
    "Select Month Range",
    min_value=months_sorted[0],
    max_value=months_sorted[-1],
    value=(months_sorted[0], months_sorted[-1])
)

# Filter by date
start_period = pd.Period(month_range[0], freq='M')
end_period = pd.Period(month_range[1], freq='M')
mask = (df["Month"] >= start_period) & (df["Month"] <= end_period)
df_filtered = df[mask]

# --- Dashboard Content ---
st.title("💸 Personal Budget Dashboard")

if df_filtered.empty:
    st.warning("No data available for the selected period.")
else:
    st.subheader("📊 Category-wise Spending")
    fig1 = px.pie(df_filtered, names="Category", values="Amount", title="Spending by Category")
    st.plotly_chart(fig1)

    # Daily & Cumulative Spending
    st.subheader("📈 Daily & Cumulative Spending Trend")
    daily = df_filtered.groupby("Date")["Amount"].sum().reset_index()
    daily["Cumulative"] = daily["Amount"].cumsum()
    fig2 = px.line(daily, x="Date", y=["Amount", "Cumulative"], 
                   labels={"value": "Amount", "variable": "Type"})
    st.plotly_chart(fig2)

    # Budget vs Actual Bar Chart
    st.subheader(f"📅 Budget vs Actual for '{category}'")
    monthly_cat = df_filtered[df_filtered["Category"] == category].groupby("Month")["Amount"].sum().reset_index()
    monthly_cat["Month"] = monthly_cat["Month"].astype(str)
    monthly_cat = monthly_cat.sort_values("Month")

    cat_budget = budget[budget["Category"] == category]["Budget"].values[0]
    monthly_cat["Budget"] = cat_budget

    fig3 = px.bar(monthly_cat, x="Month", y=["Amount", "Budget"], barmode="group")
    st.plotly_chart(fig3)

    # Alert
    total_spent = monthly_cat["Amount"].sum()
    expected_budget = cat_budget * len(monthly_cat)
    diff = round(abs(total_spent - expected_budget), 2)

    if total_spent > expected_budget:
        st.error(f"🚨 Alert: Over Budget by ₹{diff}")
    else:
        st.success(f"✅ Under Budget by ₹{diff}")

    # Show data preview
    st.subheader("🔍 Data Preview")
    st.dataframe(df_filtered[["Date", "Category", "Amount"]].sort_values("Date").head(10))