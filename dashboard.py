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
st.header(f"{selected_filename}")

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
    plot_configs = []

    # Header for the plot controls
    h1, h2, h3, h4, h5 = st.columns([1, 6, 6, 1, 1])
    h1.markdown("**#**")
    h2.markdown("**Left Axis**")
    h3.markdown("**Right Axis**")
    h4.markdown("**Norm**")
    h5.markdown("**Del**")

    for i, pid in enumerate(st.session_state['plot_ids']):
        c1, c2, c3, c4, c5 = st.columns([1, 6, 6, 1, 1])
        
        with c1:
            st.write(f"**{i+1}**")
        with c2:
            selected_signals_y1 = st.multiselect("Left Axis", options=all_signals, key=f"plot_{pid}_signals", label_visibility="collapsed")
        with c3:
            selected_signals_y2 = st.multiselect("Right Axis", options=all_signals, key=f"plot_{pid}_signals_y2", label_visibility="collapsed")
        with c4:
            normalize = st.checkbox("Norm", key=f"norm_{pid}", label_visibility="collapsed")
        with c5:
            if st.button("❌", key=f"btn_del_{pid}"):
                plots_to_remove.append(pid)

        if selected_signals_y1 or selected_signals_y2:
            plot_configs.append({
                "y1": selected_signals_y1,
                "y2": selected_signals_y2,
                "norm": normalize,
                "title": f"Plot {i+1}"
            })

    if st.button("Add New Plot", type="primary"):
        new_id = st.session_state['next_plot_id']
        st.session_state['plot_ids'].append(new_id)
        st.session_state['next_plot_id'] += 1
        st.session_state[f"plot_{new_id}_signals"] = []
        st.session_state[f"plot_{new_id}_signals_y2"] = []
        st.rerun()

    # --- RENDER COMBINED PLOT ---
    if plot_configs and not plots_to_remove:
        rows = len(plot_configs)
        subplot_titles = [config['title'] for config in plot_configs]

        fig = make_subplots(
            rows=rows, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05,
            subplot_titles=subplot_titles,
            specs=[[{"secondary_y": True}] for _ in range(rows)]
        )

        for i, config in enumerate(plot_configs):
            row = i + 1
            normalize = config['norm']
            
            def add_trace(signal, is_secondary):
                y_data = df[signal]
                custom_data = None
                hover_template = None

                if normalize:
                    min_val = y_data.min()
                    max_val = y_data.max()
                    if max_val != min_val:
                        y_data = (y_data - min_val) / (max_val - min_val)
                    else:
                        y_data = y_data - min_val
                    
                    custom_data = df[signal]
                    hover_template = "%{y:.2f} (Norm)<br>Val: %{customdata:.2f}"

                fig.add_trace(
                    go.Scatter(x=df['Time'], y=y_data, name=signal, customdata=custom_data, hovertemplate=hover_template),
                    row=row, col=1, secondary_y=is_secondary
                )

            for signal in config['y1']: add_trace(signal, False)
            for signal in config['y2']: add_trace(signal, True)

            fig.update_yaxes(title_text="Left Axis", row=row, col=1, secondary_y=False)
            if config['y2']:
                fig.update_yaxes(title_text="Right Axis", row=row, col=1, secondary_y=True, showgrid=False)

        fig.update_layout(
            height=300 * rows, margin=dict(l=0, r=0, t=40, b=20), hovermode="x unified", template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

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