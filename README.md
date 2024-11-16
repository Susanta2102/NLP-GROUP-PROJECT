# Security Policy and Compliance Automation Using NLP

## Project Overview
This project focuses on automating the extraction and enforcement of security policies and compliance requirements from regulatory documents using Natural Language Processing (NLP). The tool uses advanced NLP techniques to identify, categorize, and check compliance with security policies, particularly for frameworks such as GDPR, HIPAA, and PCI DSS. The goal is to develop an automated solution to assess compliance, extract relevant information, and enforce security and privacy standards.

## Objectives
- To develop a method for extracting relevant information from privacy policy texts.
- To apply NLP models to classify text according to GDPR compliance criteria.
- To evaluate the effectiveness of different NLP models in identifying GDPR principles.

## Primary Functions of the Application

### Natural Language Processing for Compliance Check
The app uses NLP models (SentenceTransformers and PyTorch) to analyze text data, which likely involves identifying phrases, sentences, or policies that relate to GDPR requirements.
Sentence tokenization, powered by NLTK, helps break down text into smaller, analyzable units, enabling the model to analyze content more accurately.

### User Interaction via Streamlit
Streamlit provides an interface for users to input text, which the app processes for GDPR compliance. This user-friendly interface likely includes text input fields, buttons, and checkboxes to configure the analysis.

### Visualization of Analysis Results
Plotly is used to create interactive graphs or visual elements, making it easier for users to interpret the analysis results. The visuals might include metrics related to the text’s compliance level, highlight compliance issues, or show recommendations.

### GDPR Compliance Reporting
The app may provide a summary or compliance score based on text analysis, giving users insights into how their text aligns with GDPR standards and pinpointing areas that may need revision.

## Demo Video
You can watch the demo of the project in action by clicking the link below:
[Demo Video to run the script](https://github.com/Susanta2102/NLP-GROUP-PROJECT/blob/main/Demo%20Video%20to%20run%20the%20script.mp4)
[Demo Video](https://github.com/Susanta2102/NLP-GROUP-PROJECT/blob/main/Demo.mp4)
## Installation

### Prerequisites
To run the project, you will need the following software:
- **Python**
- **PyTorch**
- **spaCy**
- **Transformers**
- **NLTK**
- **Compliance Libraries** (for regulatory documents)

### Setup
To set up the project on your machine, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/Susanta2102/NLP-GROUP-PROJECT
   cd NLP-GROUP-PROJECT
   pip install -r requirements.txt


```bash
python gdpr_compliance_checker.py sample.txt
```
![Report Sample](https://github.com/Susanta2102/NLP-GROUP-PROJECT/raw/main/1.png)

or
```bash
streamlit run main.py
```
![Streamlit Interface](https://github.com/Susanta2102/NLP-GROUP-PROJECT/raw/main/2.png)
![Streamlit Interface](https://github.com/Susanta2102/NLP-GROUP-PROJECT/raw/main/3.png)
![Streamlit Interface](https://github.com/Susanta2102/NLP-GROUP-PROJECT/raw/main/4.png)


## Contributions
- **SusantA Baidya**: msa23009@iiitl.ac.in
- **Anjali Tamta**  : msa23026@iiitl.ac.in
- **Sapna Kumari**  : msa23001@iiitl.ac.in
- **Akanksha Kumari** : msa23003@iiitl.ac.in
- **Vikrant Kumad** : msa23016@iiitl.ac.in
