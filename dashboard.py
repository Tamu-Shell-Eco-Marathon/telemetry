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


# 1. LOG CATEGORY & FILE SELECTOR
SCRIPT_DIR = Path(__file__).parent.absolute()
LOGS_DIR = SCRIPT_DIR / "logs"

log_categories = {
    "Final": LOGS_DIR / "final",
    "Raw": LOGS_DIR / "raw",
    "Saved": LOGS_DIR / "saved",
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

    # --- Session State Management ---
    if 'plot_ids' not in st.session_state:
        st.session_state['plot_ids'] = []
    if 'next_plot_id' not in st.session_state:
        st.session_state['next_plot_id'] = 0

    all_signals = [col for col in df.columns if col != 'Time']

    # Sanitize signals: Remove selected signals that don't exist in the new file
    for pid in st.session_state['plot_ids']:
        for key in [f"plot_{pid}_signals", f"plot_{pid}_signals_y2"]:
            if key in st.session_state:
                st.session_state[key] = [s for s in st.session_state[key] if s in all_signals]
    
    # --- PLOT AREA ---

    plots_to_remove = []

    for pid in st.session_state['plot_ids']:
        # Use a bordered container to group plot controls
        with st.container(border=True):
            c1, c2 = st.columns([0.9, 0.1])
            
            with c1:
                col_y1, col_y2 = st.columns(2)
                with col_y1:
                    selected_signals_y1 = st.multiselect(
                        "Left Axis",
                        options=all_signals,
                        key=f"plot_{pid}_signals", # Re-using the original key for the Left Axis
                    )
                with col_y2:
                    selected_signals_y2 = st.multiselect(
                        "Right Axis",
                        options=all_signals,
                        key=f"plot_{pid}_signals_y2",
                    )
            
            if c2.button("❌", key=f"btn_del_{pid}"):
                plots_to_remove.append(pid)

            if selected_signals_y1 or selected_signals_y2:
                fig = go.Figure()

                # Add traces for Left Axis
                for signal in selected_signals_y1:
                    fig.add_trace(go.Scatter(x=df['Time'], y=df[signal], name=signal, yaxis="y1"))

                # Add traces for Right Axis
                for signal in selected_signals_y2:
                    fig.add_trace(go.Scatter(x=df['Time'], y=df[signal], name=signal, yaxis="y2"))
                
                # Define layout update dictionary
                layout_update = {
                    'height': 350,
                    'margin': dict(l=0, r=0, t=40, b=20),
                    'hovermode': "x unified",
                    'template': "plotly_dark",
                    'legend': dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    'yaxis': {'title': 'Left Axis'},
                }

                # Add Right Axis to layout if it's being used
                if selected_signals_y2:
                    layout_update['yaxis2'] = {
                        'title': 'Right Axis',
                        'overlaying': 'y',
                        'side': 'right',
                        'showgrid': False,
                    }

                fig.update_layout(**layout_update)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No signals selected. Use the dropdowns above to add traces to this plot.")

    if st.button("Add New Plot", type="primary"):
        new_id = st.session_state['next_plot_id']
        st.session_state['plot_ids'].append(new_id)
        st.session_state['next_plot_id'] += 1
        st.session_state[f"plot_{new_id}_signals"] = []
        st.session_state[f"plot_{new_id}_signals_y2"] = []
        st.rerun()

    if plots_to_remove:
        for pid in plots_to_remove:
            st.session_state['plot_ids'].remove(pid)
            del st.session_state[f"plot_{pid}_signals"]
            if f"plot_{pid}_signals_y2" in st.session_state:
                del st.session_state[f"plot_{pid}_signals_y2"]
        st.rerun()

    with st.expander("View Raw Data"):
        st.dataframe(df)

except Exception as e:
    st.error(f"Error reading file: {e}")