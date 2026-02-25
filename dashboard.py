import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob

# Set the page layout to wide
st.set_page_config(layout="wide", page_title="DIS Telemetry Viewer")

st.title("Shell Eco-marathon Telemetry")

# --- SIDEBAR: CONTROLS ---
st.sidebar.header("Data Management")

st.sidebar.info("Logs are automatically synced from GitHub. To add new logs, run the local sync script.")

# 1. FILE SELECTOR
# Look for CSVs directly in the repo's 'logs' folder
# (Make sure you create a folder named 'logs' in your GitHub repo!)
log_files = glob.glob("logs/*.csv")

if not log_files:
    st.info("No logs found in the GitHub repository's 'logs' folder.")
    st.stop()

# Sort by newest first 
# Note: In the cloud, getmtime might be the time the server cloned the repo. 
# It's usually safer to sort alphabetically if your logs have timestamps in the filename (e.g., log_20260224.csv)
log_files.sort(reverse=True) 

selected_file = st.sidebar.selectbox("Select Test Run:", log_files)

# --- MAIN AREA: DATA VISUALIZATION ---

@st.cache_data
def load_data(filepath):
    return pd.read_csv(filepath)

try:
    df = load_data(selected_file)
    
    if 'Time' not in df.columns:
        df['Time'] = df.index

    # Let the user pick which columns to graph (excluding Time)
    all_signals = [col for col in df.columns if col != 'Time']
    default_signals = all_signals[:2] if len(all_signals) >= 2 else all_signals
    
    selected_signals = st.multiselect(
        "Select Signals to Plot:", 
        options=all_signals,
        default=default_signals
    )

    if not selected_signals:
        st.warning("Please select at least one signal to plot.")
    else:
        # Create a subplot with shared X-axis
        fig = make_subplots(
            rows=len(selected_signals), cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=selected_signals
        )

        for i, signal in enumerate(selected_signals):
            fig.add_trace(
                go.Scatter(x=df['Time'], y=df[signal], name=signal),
                row=i+1, col=1
            )

        fig.update_layout(
            height=300 * len(selected_signals),
            hovermode="x unified",
            showlegend=False,
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("View Raw Data"):
            st.dataframe(df)

except Exception as e:
    st.error(f"Error reading file: {e}")