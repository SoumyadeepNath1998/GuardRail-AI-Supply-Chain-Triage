import streamlit as st
import numpy as np
import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import time

st.set_page_config(page_title="GuardRail AI - Supply Chain Risk Triage", layout="wide")

def generate_noisy_telemetry():
    np.random.seed(int(time.time()) % 1000)
    suppliers = ["Global_Chips_Inc", "Apex_Logistics", "Euro_Forgings_Ltd", "Pacific_Transit"]
    data = []
    for supplier in suppliers:
        data_packet_drop = np.random.rand() < 0.20 
        if data_packet_drop:
            data.append({"Supplier": supplier, "Transit_Delay_Hrs": np.nan, "IoT_Ping_Latency_ms": np.nan, "Cyber_Threat_Alerts": np.random.randint(2, 5), "Data_Integrity_Flag": 0})
        else:
            data.append({"Supplier": supplier, "Transit_Delay_Hrs": float(np.random.normal(12, 4)), "IoT_Ping_Latency_ms": float(np.random.exponential(150)), "Cyber_Threat_Alerts": int(np.random.choice([0, 1, 2], p=[0.7, 0.2, 0.1])), "Data_Integrity_Flag": 1})
    return pd.DataFrame(data)

def calculate_conformal_risk_intervals(df, significance_level=0.05):
    mock_calibration_scores = np.array([1.2, 2.5, 0.8, 4.1, 3.3, 1.9, 0.5, 2.2, 5.0, 1.7])
    n_cal = len(mock_calibration_scores)
    q_index = min(max(int(np.ceil((n_cal + 1) * (1 - significance_level))), 1), n_cal) - 1
    quantile_error = np.sort(mock_calibration_scores)[q_index]
    
    intervals = []
    for _, row in df.iterrows():
        if row["Data_Integrity_Flag"] == 0:
            base_risk_score = 65.0 
            uncertainty_buffer = quantile_error * 4.5 
        else:
            base_risk_score = (row["Transit_Delay_Hrs"] * 2) + (row["Cyber_Threat_Alerts"] * 15)
            uncertainty_buffer = quantile_error * 1.2
        r_min = max(0.0, base_risk_score - uncertainty_buffer)
        r_max = min(100.0, base_risk_score + uncertainty_buffer)
        intervals.append((round(r_min, 2), round(r_max, 2)))
    df["Risk_Interval"] = intervals
    df["Max_Risk"] = [i[1] for i in intervals]
    return df

def execute_or_tools_rerouting():
    distance_matrix = [[0, 15, 22, 35], [15, 0, 12, 40], [22, 12, 0, 20], [35, 40, 20, 0]]
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    def distance_callback(from_index, to_index):
        return distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))
        return route
    return [0, 1, 2, 0]

st.title("🛡️ GuardRail AI: Supply Chain Triage Framework")
col1, col2 = st.columns([1, 3])
with col1:
    st.markdown("### ⚙️ Engine Configurations")
    threshold = st.slider("Risk Action Threshold (R_max Boundary)", 40.0, 90.0, 70.0)
    significance = st.slider("Conformal Error Bound", 0.01, 0.10, 0.05)
    st.button("🔄 Ingest Real-Time Telemetry Stream")

telemetry_data = generate_noisy_telemetry()
calibrated_data = calculate_conformal_risk_intervals(telemetry_data, significance_level=significance)

with col2:
    st.markdown("### 📊 Live Risk Triage Board")
    st.dataframe(calibrated_data, use_container_width=True)

st.markdown("---")
st.markdown("### 🚚 Automated Mitigations Pipeline (Google OR-Tools Execution)")
optimized_path = execute_or_tools_rerouting()
st.info(f"📍 **Optimized Safe Node Sequence Trajectory:** {' ➔ '.join([str(n) for n in optimized_path])}")
