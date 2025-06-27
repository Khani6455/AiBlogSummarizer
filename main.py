from flask import Flask, render_template_string, request, send_file
import requests
import os
from dotenv import load_dotenv
from io import BytesIO
from fpdf import FPDF

load_dotenv()
app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "meta-llama/llama-3.1-8b-instruct:free"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Blog Summarizer</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: #f8f9fa;
            padding: 3rem;
            color: #333;
        }
        h1 {
            text-align: center;
            color: #111;
        }
        form, .output-box {
            max-width: 800px;
            margin: 2rem auto;
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        textarea {
            width: 100%;
            padding: 1rem;
            font-size: 1rem;
            border-radius: 8px;
            border: 1px solid #ccc;
            transition: border-color 0.3s;
        }
        textarea:focus {
            border-color: #007bff;
            outline: none;
        }
        button {
            padding: 1rem 2rem;
            font-size: 1rem;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #0056b3;
        }
        .actions {
            margin-top: 1rem;
        }
        .output-box {
            white-space: pre-wrap;
        }
        #loader {
            text-align: center;
            display: none;
        }
        .copy-btn, .pdf-btn {
            background-color: #28a745;
            margin-left: 0.5rem;
        }
        .copy-btn:hover, .pdf-btn:hover {
            background-color: #1e7e34;
        }
    </style>
    <script>
        function showLoader() {
            document.getElementById('loader').style.display = 'block';
        }
        function copyText() {
            const summary = document.getElementById("summary-text").innerText;
            navigator.clipboard.writeText(summary);
            alert("Summary copied to clipboard!");
        }
    </script>
</head>
<body>
    <h1>🧠 AI Blog Summarizer</h1>
    <form method="POST" onsubmit="showLoader()">
        <textarea name="content" rows="10" placeholder="Paste your blog article here..." required>{{ content }}</textarea>
        <div class="actions">
            <button type="submit">Summarize</button>
        </div>
    </form>

    <div id="loader">⏳ Summarizing... Please wait.</div>

    {% if summary %}
    <div class="output-box">
        <h3>🔍 Summary:</h3>
        <div id="summary-text">{{ summary }}</div>
        <div class="actions">
            <button class="copy-btn" onclick="copyText()">📋 Copy</button>
            <form method="POST" action="/download" style="display:inline;">
                <input type="hidden" name="summary" value="{{ summary }}">
                <button class="pdf-btn" type="submit">⬇️ Download PDF</button>
            </form>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

def summarize_with_openrouter(content):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes blog articles in simple language."},
            {"role": "user", "content": f"Please summarize the following blog post:\n\n{content}"}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.route("/", methods=["GET", "POST"])
def index():
    summary = ""
    content = ""
    if request.method == "POST":
        content = request.form.get("content", "")
        if content:
            summary = summarize_with_openrouter(content)
    return render_template_string(HTML_TEMPLATE, summary=summary, content=content)

@app.route("/download", methods=["POST"])
def download():
    summary = request.form.get("summary", "")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in summary.split("\n"):
        pdf.multi_cell(0, 10, line)
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="summary.pdf", mimetype="application/pdf")

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=3000)
