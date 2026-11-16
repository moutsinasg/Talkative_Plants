import glob
import os
import re
from datetime import datetime
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Talkative Plants IoT Dashboard", page_icon="🌱", layout="wide"
)

# App Header
st.title("🌱 Talkative Plants: Real-Time Crop Water Status Demo")
st.markdown(
    """
This dashboard visualizes real-time soil moisture and sensor telemetry from demonstration pots. 
It highlights how integrated data interpretation guides precise irrigation timing.
"""
)


# Helper function to load and parse the latest .dat log file
@st.cache_data(ttl=2)
def load_latest_data():
  dat_files = glob.glob("*.dat")
  if not dat_files:
    return None, None
  latest_file = max(dat_files, key=os.path.getmtime)

  timestamp_pattern = re.compile(r"^\d{2}:\d{2}:\d{2}:\d{2}:\d{2}:\d{2}")
  valid_lines = []

  try:
    with open(latest_file, "r") as f:
      for line in f:
        line_str = line.strip()
        if timestamp_pattern.match(line_str):
          valid_lines.append(line_str.split())
  except Exception as e:
    st.error(f"Error reading file {latest_file}: {e}")
    return None, latest_file

  if not valid_lines:
    return None, latest_file

  # Build DataFrame and format columns (expecting 45 columns)
  df = pd.DataFrame(valid_lines)
  if len(df.columns) >= 45:
    df = df.iloc[:, :45]
    df.columns = [f"Col_{i+1}" for i in range(45)]
    for col in ["Col_34", "Col_29"]:
      df[col] = pd.to_numeric(df[col], errors="coerce")

  return df, latest_file


# Sidebar Controls & Status
st.sidebar.header("⚙️ Demo Controls")
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=True)

if auto_refresh:
  st.sidebar.info("🔄 Live monitoring active (refreshing every 5s)...")
  st.rerun()

# Load Data
df, active_file = load_latest_data()

if df is not None and not df.empty:
  latest_row = df.iloc[-1]
  col_34_val = latest_row.get("Col_34", 0)
  col_29_val = latest_row.get("Col_29", 0)

  # Thirsty Threshold Logic (matches talking_plants_v2.py threshold < 300)
  is_thirsty = col_34_val < 300

  # Visual Status Banner
  if is_thirsty:
    st.error(
        "⚠️ **Plant Status: THIRSTY** — Soil moisture is below critical threshold"
        " (< 300). Irrigation required!"
    )
  else:
    st.success(
        "✅ **Plant Status: OPTIMAL** — Adequate moisture available for uptake."
    )

  # Key Metrics Display
  m1, m2, m3 = st.columns(3)
  m1.metric(
      label="Soil Moisture Index (Col 34)",
      value=f"{col_34_val:.1f}",
      delta="Thirsty (<300)" if is_thirsty else "Adequate (>=300)",
      delta_inverse=True,
  )
  m2.metric(
      label="Biopotential Stress Index (Col 29)", value=f"{col_29_val:.2f}"
  )
  m3.metric(
      label="Active Log File",
      value=os.path.basename(active_file) if active_file else "None",
  )

  # Telemetry Charts
  st.subheader("📈 Real-Time Sensor Telemetry")
  tab1, tab2 = st.tabs(["Soil Moisture Trend", "Biopotential Trend"])

  with tab1:
    st.line_chart(df["Col_34"].astype(float))
    st.caption(
        "Tracking sensor readings from Column 34. Values dropping below 300"
        " trigger voice alerts."
    )

  with tab2:
    st.line_chart(df["Col_29"].astype(float))
    st.caption("Secondary physiological indicator (biopotential).")

  # Raw Data Expander
  with st.expander("🔍 View Raw Telemetry Stream"):
    st.dataframe(df.tail(20), use_container_width=True)

else:
  st.warning(
      "⏳ Waiting for incoming telemetry data. Ensure `talking_plants_v2.py` is"
      " running and logging `.dat` files locally."
  )

# Educational Footer (Aligned with Open House Narrative)
st.markdown("---")
with st.expander("🌾 About the Demo & Scientific Context"):
  st.markdown(
      """
    * **Holistic Monitoring:** Adequate soil water does not automatically guarantee plant uptake[cite: 1]. 
    * **Soil Properties:** Mechanical properties such as texture, hydraulic conductivity, and bulk density directly affect water availability[cite: 1].
    * **Integrated Approach:** This demo combines sensor measurements with registered soil properties to evaluate true crop water status and optimize irrigation timing[cite: 1].
    """
  )
