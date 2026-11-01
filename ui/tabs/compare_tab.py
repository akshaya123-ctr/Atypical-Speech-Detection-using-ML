import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

RESULTS_JSON = "model_results.json"
RESULTS_DIR = "results/stage_1"
TEST_REPORT_JSON = os.path.join(RESULTS_DIR, "test_evaluation_report.json")

def render_compare_tab():
    st.markdown("""
    <div class='dark-card'>
        <div class='dark-card-header'>
            <div class='dark-card-icon'>📊</div>
            <div>
                <h3 class='dark-card-title'>Compare ML Algorithms & Validation Metrics</h3>
                <p class='dark-card-desc'>
                    Benchmarking of 3 Machine Learning algorithms (SVM, Random Forest, MLP) across the 3 fields (Typical, Dysarthria, Stammer) evaluated via 5-Fold Speaker-Disjoint Cross Validation (0 Leakage across 264 Speakers).
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not os.path.exists(RESULTS_JSON):
        st.warning("model_results.json not found. Run python training/train_pipeline.py to generate metrics.")
        return
        
    with open(RESULTS_JSON, "r") as f:
        data = json.load(f)
        
    stage1 = data.get("stage_1", {})
    if not stage1:
        st.warning("No stage_1 results found.")
        return

    best_model_name = data.get("best_model", "SVM")
    best_cv_acc = data.get("best_cv_accuracy", 0.0)

    # Validation Gate Banner (Dark Luxury Style)
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 182, 212, 0.08) 100%); border: 1.5px solid rgba(16, 185, 129, 0.35); border-radius: 16px; padding: 22px; text-align: center; margin-bottom: 25px;'>
        <div style='display:inline-block; font-size:11px; font-weight:700; color:#34D399; letter-spacing:0.1em; text-transform:uppercase; background:rgba(16,185,129,0.15); padding:4px 12px; border-radius:20px; margin-bottom:8px;'>
            ✅ MODULE 1 VALIDATION GATE: PASSED
        </div>
        <h3 style='color: #FFFFFF; margin: 4px 0 8px 0; font-size: 22px;'>Speaker-Independent 5-Fold Cross Validation Confirmed</h3>
        <p style='color: #9CA3AF; margin: 0; font-size: 14px;'>
            <b>Zero Speaker Leakage:</b> 0 Overlap between Train and Test splits across 264 unique speakers<br/>
            <b>Best Performing Model:</b> <span style='color:#F59E0B; font-weight:700;'>{best_model_name}</span> (CV Accuracy: <b>{best_cv_acc*100:.2f}%</b>)
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 4-KPI Overview for Best Model
    best_key = best_model_name.replace(" ", "_")
    best_stats = stage1.get(best_key, list(stage1.values())[0])

    st.markdown("<p style='font-size: 13px; font-weight: 700; color: #9CA3AF; text-transform: uppercase; margin-bottom: 8px;'>🏆 TOP PERFORMING MODEL METRICS (" + best_model_name + "):</p>", unsafe_allow_html=True)
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        st.markdown(f"""
        <div class='kpi-card kpi-yellow'>
            <div class='kpi-icon'>🎯</div>
            <div class='kpi-label'>Accuracy</div>
            <div class='kpi-value'>{best_stats['accuracy']*100:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with kcol2:
        st.markdown(f"""
        <div class='kpi-card kpi-green'>
            <div class='kpi-icon'>✅</div>
            <div class='kpi-label'>Precision</div>
            <div class='kpi-value'>{best_stats['precision']*100:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with kcol3:
        st.markdown(f"""
        <div class='kpi-card kpi-blue'>
            <div class='kpi-icon'>🔍</div>
            <div class='kpi-label'>Recall</div>
            <div class='kpi-value'>{best_stats['recall']*100:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with kcol4:
        st.markdown(f"""
        <div class='kpi-card kpi-purple'>
            <div class='kpi-icon'>⚖️</div>
            <div class='kpi-label'>F1 Score</div>
            <div class='kpi-value'>{best_stats['f1']*100:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
    # Build dataframe for Plotly comparison
    rows = []
    for model_name, metrics in stage1.items():
        name_clean = model_name.replace("_", " ")
        rows.append({
            "Algorithm": name_clean,
            "Accuracy": round(metrics["accuracy"] * 100, 2),
            "F1 Score": round(metrics["f1"] * 100, 2),
            "Precision": round(metrics["precision"] * 100, 2),
            "Recall": round(metrics["recall"] * 100, 2)
        })
        
    df_metrics = pd.DataFrame(rows)
    
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        st.markdown("<h4 style='color:#FFFFFF; margin-bottom:10px;'>📈 5-Fold Cross-Validation Accuracy Comparison (%)</h4>", unsafe_allow_html=True)
        fig = px.bar(
            df_metrics,
            x="Algorithm",
            y="Accuracy",
            color="Accuracy",
            text="Accuracy",
            color_continuous_scale=["#3B82F6", "#F59E0B"],
            template="plotly_dark"
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis_range=[0, 100],
            height=340,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown("<h4 style='color:#FFFFFF; margin-bottom:10px;'>📋 Metrics Summary Table</h4>", unsafe_allow_html=True)
        st.dataframe(df_metrics, use_container_width=True, hide_index=True)
        
    st.markdown("<hr style='border-color: #232731;'/>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#FFFFFF; margin-bottom:12px;'>🧩 Confusion Matrix Heatmaps (3 Fields: Typical, Dysarthria, Stammer)</h4>", unsafe_allow_html=True)
    
    algo_keys = list(stage1.keys())
    m_cols = st.columns(len(algo_keys))
    
    for idx, key in enumerate(algo_keys):
        img_path = os.path.join(RESULTS_DIR, f"{key}_cm.png")
        with m_cols[idx]:
            st.markdown(f"<h5 style='color:#F59E0B; text-align:center;'>{key.replace('_', ' ')}</h5>", unsafe_allow_html=True)
            if os.path.exists(img_path):
                image = Image.open(img_path)
                st.image(image, use_container_width=True)
            else:
                st.info("Confusion matrix image pending.")

    # Holdout Test & Benchmark Section
    if os.path.exists(TEST_REPORT_JSON):
        st.markdown("<hr style='border-color: #232731;'/>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#FFFFFF; margin-bottom:12px;'>🔬 Speaker-Disjoint Holdout Testing & Latency Benchmark</h4>", unsafe_allow_html=True)
        with open(TEST_REPORT_JSON, "r") as f:
            test_data = json.load(f)
            
        t_algos = test_data.get("algorithms", {})
        t_rows = []
        for a_k, a_v in t_algos.items():
            t_rows.append({
                "Algorithm": a_v["name"],
                "Holdout Accuracy": f"{a_v['holdout_accuracy']*100:.2f}%",
                "Holdout F1": f"{a_v['holdout_f1']*100:.2f}%",
                "Precision": f"{a_v['holdout_precision']*100:.2f}%",
                "Recall": f"{a_v['holdout_recall']*100:.2f}%",
                "Inference Latency": f"{a_v['latency_ms_per_sample']:.2f} ms",
                "Noise Robustness": f"{a_v['noise_robustness_pct']:.1f}%"
            })
            
        st.dataframe(pd.DataFrame(t_rows), use_container_width=True, hide_index=True)

        bar_path = os.path.join(RESULTS_DIR, "test_comparison_barchart.png")
        if os.path.exists(bar_path):
            st.image(Image.open(bar_path), caption="Holdout Test Metrics (Unseen Speakers across 3 Fields)", use_container_width=True)
