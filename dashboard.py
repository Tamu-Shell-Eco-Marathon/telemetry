import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob
from pathlib import Path

# Set the page layout to wide
st.set_page_config(layout="wide", page_title="DIS Telemetry Viewer")

st.title("Shell Eco-marathon Telemetry Viewer")

# --- SIDEBAR: CONTROLS ---
st.sidebar.header("Data Management")

st.sidebar.info("Logs are automatically synced from GitHub. To add new logs, run the local sync script.")

# 1. LOG CATEGORY & FILE SELECTOR
SCRIPT_DIR = Path(__file__).parent.absolute()
LOGS_DIR = SCRIPT_DIR / "logs"

log_categories = {
    "Processed (Final)": LOGS_DIR / "final",
    "Raw (Unprocessed)": LOGS_DIR / "raw",
    "Saved (Important)": LOGS_DIR / "saved",
}

selected_category = st.sidebar.selectbox(
    "Select Log Category:", 
    options=list(log_categories.keys()),
    index=0
)

current_dir = log_categories[selected_category]

# Get files using pathlib
log_files = list(current_dir.glob("*.csv")) if current_dir.exists() else []

if not log_files:
    st.info(f"No logs found in {selected_category}.")
    st.stop()

# Sort by filename (descending)
log_files.sort(key=lambda p: p.name, reverse=True)

file_map = {p.name: p for p in log_files}
selected_filename = st.sidebar.selectbox("Select Test Run:", list(file_map.keys()))
selected_file = file_map[selected_filename]

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