import streamlit as st
import torch
from sentence_transformers import SentenceTransformer
from torch import nn
import nltk
from nltk.tokenize import sent_tokenize
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from pathlib import Path
import base64
from datetime import datetime
import json
import time
import textwrap
import numpy as np

# Attempt to download the Punkt tokenizer if it's not available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Configure Streamlit page
st.set_page_config(
    page_title="GDPR Compliance Analyzer Pro",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with enhanced styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #f5f7f9 0%, #ffffff 100%);
    }
    
    .main {
        padding: 2rem;
        font-family: 'Poppins', sans-serif;
    }
    
    .stTitle {
        font-size: 3rem !important;
        font-weight: 700 !important;
        background: linear-gradient(120deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem !important;
    }
    
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border: 1px solid #eee;
        transition: transform 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
    }
    
    .metric-card {
        text-align: center;
        padding: 1.5rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .principle-card {
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .compliant {
        background: linear-gradient(135deg, #e7f5e7 0%, #d4edda 100%);
        border-left: 4px solid #28a745;
    }
    
    .non-compliant {
        background: linear-gradient(135deg, #fff5f5 0%, #ffe6e6 100%);
        border-left: 4px solid #dc3545;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        border: none;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .sidebar-content {
        padding: 1.5rem;
        background: white;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .highlight {
        background: #f0f7ff;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        color: #1e3c72;
    }
    
    .progress-bar-container {
        width: 100%;
        height: 20px;
        background-color: #f0f0f0;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

def create_radar_chart(results):
    # Extract principles and scores
    principles = list(results.keys())
    scores = [results[p]["score"] for p in principles]
    
    # Create the radar chart
    fig = go.Figure()
    
    # Add trace for the scores
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],  # Duplicate first score to close the polygon
        theta=principles + [principles[0]],  # Duplicate first principle to close the polygon
        fill='toself',
        fillcolor='rgba(30, 60, 114, 0.2)',  # Light blue fill
        line=dict(color='#1e3c72', width=2),  # Dark blue line
        name='Compliance Score'
    ))
    
    # Add trace for the threshold
    threshold_values = [0.8] * len(principles)  # Assuming 0.8 as threshold
    fig.add_trace(go.Scatterpolar(
        r=threshold_values + [threshold_values[0]],
        theta=principles + [principles[0]],
        fill='toself',
        fillcolor='rgba(211, 211, 211, 0.2)',  # Light grey fill
        line=dict(color='grey', width=1, dash='dash'),
        name='Threshold'
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickformat='.0%',
                showline=False,
                ticks='',
                gridcolor='#E5E5E5'
            ),
            angularaxis=dict(
                showline=True,
                linecolor='#E5E5E5'
            ),
            bgcolor='white'
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=1.1,
            xanchor="left",
            x=0.1
        ),
        margin=dict(t=100),
        height=400
    )
    
    return fig

def create_sunburst_chart(compliance_results):
    # Prepare data for sunburst chart
    data = []
    for principle, details in compliance_results.items():
        status = "Compliant" if details.get("compliant") else "Non-compliant"
        score = details.get("score", 0) if details.get("compliant") else 0
        data.append({
            "principle": principle,
            "status": status,
            "score": score
        })
    
    df = pd.DataFrame(data)
    
    fig = px.sunburst(
        df,
        path=['status', 'principle'],
        values='score',
        color='status',
        color_discrete_map={
            'Compliant': '#28a745',
            'Non-compliant': '#dc3545'
        },
    )
    
    fig.update_layout(
        margin=dict(t=0, l=0, r=0, b=0),
        height=400,
    )
    
    return fig

def main():
    # Initialize policy_text with empty string
    policy_text = ""
    
    # Header section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<h1 class='stTitle'>GDPR Compliance Analyzer Pro</h1>", unsafe_allow_html=True)
        st.markdown("""
        🛡️ Advanced analysis tool for evaluating privacy policies against GDPR principles.
        Powered by machine learning and natural language processing.
        """)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Analysis Settings")
        
        
        with st.expander("📊 Visualization Options", expanded=True):
            show_radar = st.checkbox("Show Radar Chart", value=True)
            show_sunburst = st.checkbox("Show Sunburst Chart", value=True)
    
    # Input section
    st.markdown("### 📄 Input Policy")
    input_method = st.radio(
        "Choose input method:",
        ["Upload File", "Paste Text", "Use Sample"],
        horizontal=True
    )
    
    sample_text = """We are committed to protecting your privacy and handling your data in an open and transparent manner. 
    We collect and process personal data in accordance with applicable laws and regulations.
    The data we collect is limited to what is necessary for the purposes for which it is processed. 
    We ensure that personal data is accurate and kept up to date.
    We implement appropriate technical and organizational measures to ensure data security. 
    We retain personal data only for as long as necessary.
    We are accountable for demonstrating compliance with data protection principles."""

    if input_method == "Upload File":
        uploaded_file = st.file_uploader("Upload Privacy Policy (TXT)", type=['txt'])
        if uploaded_file:
            policy_text = uploaded_file.getvalue().decode()
    elif input_method == "Paste Text":
        policy_text = st.text_area("Enter policy text:", height=200)
    else:  # Use Sample
        policy_text = sample_text
        st.text_area("Sample policy text:", value=policy_text, height=200, disabled=True)
    
    if st.button("🔍 Analyze Policy", disabled=not policy_text):
        with st.spinner("🔄 Analyzing policy..."):
            # Simulate analysis for demo
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # Analysis results (simplified for demo)
            results = {
                "Lawfulness, Fairness and Transparency": {"compliant": True, "score": 0.9, "example": "Sample text"},
                "Purpose Limitation": {"compliant": True, "score": 0.85, "example": "Sample text"},
                "Data Minimization": {"compliant": False, "score": 0.6},
                "Accuracy": {"compliant": True, "score": 0.95, "example": "Sample text"},
                "Storage Limitation": {"compliant": True, "score": 0.88, "example": "Sample text"},
                "Integrity and Confidentiality": {"compliant": False, "score": 0.7},
                "Accountability": {"compliant": True, "score": 0.92, "example": "Sample text"}
            }
            
            # Results section
            st.markdown("### 📊 Analysis Results")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            compliant_count = sum(1 for r in results.values() if r["compliant"])
            
            with col1:
                st.metric("✅ Compliant", compliant_count)
            with col2:
                st.metric("❌ Non-compliant", len(results) - compliant_count)
            with col3:
                compliance_score = compliant_count / len(results) * 100
                st.metric("📈 Overall Score", f"{compliance_score:.1f}%")
            with col4:
                avg_score = np.mean([r["score"] for r in results.values() if "score" in r])
                st.metric("⭐ Average Score", f"{avg_score:.2f}")
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            if show_radar:
                with col1:
                    st.plotly_chart(create_radar_chart(results), use_container_width=True)
            
            if show_sunburst:
                with col2:
                    st.plotly_chart(create_sunburst_chart(results), use_container_width=True)
            
            # Detailed findings
            st.markdown("### 🔍 Detailed Findings")
            
            for principle, details in results.items():
                with st.expander(
                    f"{'✅' if details['compliant'] else '❌'} {principle} "
                    f"({'Compliant' if details['compliant'] else 'Non-compliant'})"
                ):
                    if details["compliant"]:
                        st.markdown(f"""
                        <div class='principle-card compliant'>
                            <h4>Status: ✅ Compliant</h4>
                            <p><strong>Confidence Score:</strong> {details['score']:.2f}</p>
                            <p><strong>Example Statement:</strong> "{details['example']}"</p>
                            <p><strong>Recommendation:</strong> Continue maintaining current standards.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='principle-card non-compliant'>
                            <h4>Status: ❌ Non-compliant</h4>
                            <p><strong>Confidence Score:</strong> {details.get('score', 0):.2f}</p>
                            <p><strong>Recommendation:</strong> Add specific clauses addressing {principle}.</p>
                            <p><strong>Suggested Improvements:</strong></p>
                            <ul>
                                <li>Include explicit statements about {principle}</li>
                                <li>Define clear procedures and policies</li>
                                <li>Provide specific examples of implementation</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Export options
            st.markdown("### 📑 Export Options")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Export as PDF"):
                    st.info("Generating PDF report...")
                    time.sleep(1)
                    st.success("PDF report ready!")
            
            with col2:
                if st.button("📊 Export as Excel"):
                    st.info("Generating Excel report...")
                    time.sleep(1)
                    st.success("Excel report ready!")

if __name__ == "__main__":
    main()
