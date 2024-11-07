import sys
import torch
from sentence_transformers import SentenceTransformer
from torch import nn
import nltk
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize
import webbrowser

sbert_label_descriptions = {
    0: "Lawfulness, Fairness and Transparency",
    1: "Purpose Limitation",
    2: "Data Minimization",
    3: "Accuracy",
    4: "Storage Limitation",
    5: "Integrity and Confidentiality",
    6: "Accountability",
}

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

sentence_sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
embedding_dim = sentence_sbert_model.get_sentence_embedding_dimension()

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = "cpu"

def load_model(path):
    model = SBertClassifier(embedding_dim, num_labels=7)
    # model.load_state_dict(torch.load(path))
    model.load_state_dict(torch.load(path, map_location=torch.device('cpu')))
    model.eval()
    return model

def sentence_sbert_classify_policy(policy_sentences, classifier, threshold=0.8):
    results = []
    unique_labels = set()

    for sentence in policy_sentences:
        if len(sentence.split()) > 11:
            embedding = sentence_sbert_model.encode(sentence, convert_to_tensor=True).to(device)

            with torch.no_grad():
                outputs = classifier(embedding.unsqueeze(0))
                probs = torch.sigmoid(outputs).squeeze(0)

            sentence_labels = []
            probs = probs.cpu().numpy()
            for idx, score in enumerate(probs):
                if score >= threshold:
                    label = sbert_label_descriptions.get(idx, "Unknown Label")
                    sentence_labels.append((label, score))
                    unique_labels.add(label)

            results.append((sentence, sentence_labels))
    return results, unique_labels

def generate_html_report(policy_name, results):
    non_compliant_count = sum(1 for details in results.values() if not details.get("compliant", False))
    total_principles = len(results)

    report_html = f"""
    <html>
    <head>
        <title>GDPR Compliance Report for {policy_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #4CAF50; }}
            h2 {{ color: #2196F3; }}
            p {{ font-size: 16px; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 10px; }}
            .compliant {{ color: green; }}
            .non-compliant {{ color: red; }}
            .example {{ margin-left: 20px; font-style: italic; }}
        </style>
    </head>
    <body>
        <h1>GDPR Compliance Report for {policy_name}</h1>
        <p><strong>Summary:</strong> Non-compliant with {non_compliant_count} out of {total_principles} principles evaluated.</p>

        <h2>Detailed Findings:</h2>
        <ul>
    """

    for principle, details in results.items():
        compliance_status = "Compliant" if details.get("compliant") else "Non-compliant"
        compliance_class = "compliant" if details.get("compliant") else "non-compliant"
        example_sentence = details.get("example", "Not available")

        report_html += f"""
        <li class="{compliance_class}">{principle}: {compliance_status}</li>
        """
        if details.get("compliant"):
            report_html += f"""
            <div class="example">Example: {example_sentence}</div>
            """

    report_html += "</ul>"

    if non_compliant_count > 0:
        non_compliant_principles = ", ".join([principle for principle, details in results.items() if not details.get("compliant")])
        report_html += f"""
        <h2>Recommendations:</h2>
        <p>Review the policy to align with the following principles:</p>
        <ul>
            <li>{non_compliant_principles}</li>
        </ul>
        """

    report_html += "</body></html>"
    return report_html

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 gdpr_compliance_checker.py policy.txt")
        sys.exit(1)

    policy_file = sys.argv[1]

    with open(policy_file, 'r', encoding='utf-8') as file:
        policy_content = file.read()

    preprocessed_policies_sentences = sent_tokenize(policy_content)

    # print(preprocessed_policies_sentences)   

    sentence_sbert_classifier_model = load_model('./models/sentence_sbert_model_path.pth')
    sentence_sbert_classifier_model.to(device) 

    policy_results, unique_labels = sentence_sbert_classify_policy(preprocessed_policies_sentences, sentence_sbert_classifier_model, threshold=0.8)

    best_examples = {}

    for sentence, labels in policy_results:
        for label, score in labels:
            if label not in best_examples or score > best_examples[label][1]:
                best_examples[label] = (sentence, score)

    compliance_threshold = 0.8

    sbert_sentences_policy_results = {}

    gdpr_principles = [
        "Lawfulness, Fairness and Transparency",
        "Purpose Limitation",
        "Data Minimization",
        "Accuracy",
        "Storage Limitation",
        "Integrity and Confidentiality",
        "Accountability"
    ]

    for principle in gdpr_principles:
        if principle in best_examples and best_examples[principle][1] >= compliance_threshold:
            sbert_sentences_policy_results[principle] = {
                "compliant": True,
                "example": best_examples[principle][0],
                "score": best_examples[principle][1]
            }
        else:
            sbert_sentences_policy_results[principle] = {"compliant": False}

    sbert_html_content = generate_html_report(policy_file, sbert_sentences_policy_results)

    html_file_path = f'{policy_file.rsplit(".", 1)[0]}_Compliance_Report.html'
    with open(html_file_path, 'w') as file:
        file.write(sbert_html_content)

    webbrowser.open(f'file://{html_file_path}')


