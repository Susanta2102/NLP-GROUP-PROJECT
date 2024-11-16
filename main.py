import streamlit as st
import torch
from sentence_transformers import SentenceTransformer
from torch import nn
import nltk
from nltk.tokenize import sent_tokenize
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
import base64
from io import StringIO

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Configure Streamlit page
st.set_page_config(
    page_title="GDPR Compliance Checker",
    page_icon="🔒",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7f9;
    }
    .main {
        padding: 2rem;
    }
    .st-emotion-cache-1v0mbdj.e115fcil1 {
        border-radius: 10px;
        padding: 1.5rem;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .principle-card {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .compliant {
        background-color: #e7f5e7;
        border-left: 4px solid #4CAF50;
    }
    .non-compliant {
        background-color: #fee;
        border-left: 4px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)

# SBERT label descriptions
sbert_label_descriptions = {
    0: "Lawfulness, Fairness and Transparency",
    1: "Purpose Limitation",
    2: "Data Minimization",
    3: "Accuracy",
    4: "Storage Limitation",
    5: "Integrity and Confidentiality",
    6: "Accountability",
}

# Model class definition
class SBertClassifier(nn.Module):
    def __init__(self, embedding_dim, num_labels):
        super(SBertClassifier, self).__init__()
        self.lstm = nn.LSTM(embedding_dim, 128, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(256, num_labels)

    def forward(self, embeddings):
        _, (hidden, _) = self.lstm(embeddings.unsqueeze(1))
        hidden = torch.cat((hidden[-2,:,:], hidden[-1,:,:]), dim=1)
        out = self.fc(hidden)
        return out

@st.cache_resource
def load_models():
    sentence_sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding_dim = sentence_sbert_model.get_sentence_embedding_dimension()
    device = "cpu"
    
    model = SBertClassifier(embedding_dim, num_labels=7)
    model.load_state_dict(torch.load('./models/sentence_sbert_model_path.pth', 
                                   map_location=torch.device('cpu')))
    model.eval()
    
    return sentence_sbert_model, model, device

def sentence_sbert_classify_policy(policy_sentences, classifier, sentence_sbert_model, 
                                 device, threshold=0.8):
    results = []
    unique_labels = set()
    
    progress_bar = st.progress(0)
    total_sentences = len(policy_sentences)
    
    for idx, sentence in enumerate(policy_sentences):
        if len(sentence.split()) > 11:
            embedding = sentence_sbert_model.encode(sentence, 
                                                  convert_to_tensor=True).to(device)

            with torch.no_grad():
                outputs = classifier(embedding.unsqueeze(0))
                probs = torch.sigmoid(outputs).squeeze(0)

            sentence_labels = []
            probs = probs.cpu().numpy()
            for prob_idx, score in enumerate(probs):
                if score >= threshold:
                    label = sbert_label_descriptions.get(prob_idx, "Unknown Label")
                    sentence_labels.append((label, score))
                    unique_labels.add(label)

            results.append((sentence, sentence_labels))
        
        # Update progress bar
        progress_bar.progress((idx + 1) / total_sentences)
    
    return results, unique_labels

def create_radar_chart(compliance_results):
    principles = list(compliance_results.keys())
    scores = [results.get('score', 0) if results.get('compliant', False) else 0 
             for results in compliance_results.values()]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=principles + [principles[0]],
        fill='toself',
        name='Compliance Score'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=False
    )
    
    return fig

def main():
    # Header
    st.title("🔒 GDPR Compliance Checker")
    st.markdown("""
    This tool analyzes privacy policies for GDPR compliance across seven key principles.
    Upload your policy text or paste it directly to get started.
    """)
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    threshold = st.sidebar.slider(
        "Compliance Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.8,
        step=0.05,
        help="Adjust the threshold for considering a principle as compliant"
    )
    
    # File upload and text input options
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Upload Privacy Policy (TXT)", type=['txt'])
    
    with col2:
        use_sample = st.checkbox("Use sample policy text", value=False)
    
    policy_text = st.text_area(
        "Or paste your policy text here:",
        height=200,
        disabled=use_sample
    )
    
    # Sample policy text
    sample_text = """
    We are committed to protecting your privacy and handling your data in an open and transparent manner. We collect and process personal data in accordance with applicable laws and regulations.
    The data we collect is limited to what is necessary for the purposes for which it is processed. We ensure that personal data is accurate and kept up to date.
    We implement appropriate technical and organizational measures to ensure data security. We retain personal data only for as long as necessary.
    We are accountable for demonstrating compliance with data protection principles.
    """
    
    if use_sample:
        policy_text = sample_text
    elif uploaded_file:
        policy_text = StringIO(uploaded_file.getvalue().decode()).read()
    
    if st.button("Analyze Policy", disabled=not (policy_text or uploaded_file)):
        with st.spinner("Analyzing policy for GDPR compliance..."):
            # Load models
            sentence_sbert_model, classifier_model, device = load_models()
            
            # Process policy
            sentences = sent_tokenize(policy_text)
            results, unique_labels = sentence_sbert_classify_policy(
                sentences, 
                classifier_model,
                sentence_sbert_model,
                device,
                threshold
            )
            
            # Prepare results
            best_examples = {}
            for sentence, labels in results:
                for label, score in labels:
                    if label not in best_examples or score > best_examples[label][1]:
                        best_examples[label] = (sentence, score)
            
            policy_results = {}
            for principle in sbert_label_descriptions.values():
                if principle in best_examples and best_examples[principle][1] >= threshold:
                    policy_results[principle] = {
                        "compliant": True,
                        "example": best_examples[principle][0],
                        "score": best_examples[principle][1]
                    }
                else:
                    policy_results[principle] = {"compliant": False}
            
            # Display results
            st.markdown("### Analysis Results")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            compliant_count = sum(1 for r in policy_results.values() if r["compliant"])
            
            with col1:
                st.metric("Compliant Principles", compliant_count)
            with col2:
                st.metric("Non-compliant Principles", len(policy_results) - compliant_count)
            with col3:
                compliance_score = compliant_count / len(policy_results) * 100
                st.metric("Overall Compliance", f"{compliance_score:.1f}%")
            
            # Radar chart
            st.plotly_chart(create_radar_chart(policy_results), use_container_width=True)
            
            # Detailed results
            st.markdown("### Detailed Findings")
            
            for principle, details in policy_results.items():
                compliance_class = "compliant" if details["compliant"] else "non-compliant"
                with st.expander(f"{principle} - {'✅ Compliant' if details['compliant'] else '❌ Non-compliant'}"):
                    if details["compliant"]:
                        st.markdown(f"""
                        <div class='principle-card compliant'>
                            <strong>Status:</strong> Compliant<br>
                            <strong>Score:</strong> {details['score']:.2f}<br>
                            <strong>Example:</strong> "{details['example']}"
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='principle-card non-compliant'>
                            <strong>Status:</strong> Non-compliant<br>
                            <strong>Recommendation:</strong> Add specific clauses addressing {principle}
                        </div>
                        """, unsafe_allow_html=True)
            
            # Export options
            st.markdown("### Export Results")
            if st.button("Generate PDF Report"):
                st.warning("PDF export functionality would be implemented here")

if __name__ == "__main__":
    main()
