import streamlit as st
import base64
import json
import os
from litellm import completion

# ----------- CONFIG -----------
api_key = st.secrets["GEMINI_API_KEY"]
os.environ["GEMINI_API_KEY"] = api_key
GEMINI_MODEL = "gemini/gemini-1.5-flash"
st.set_page_config(page_title="Resume Analyzer AI", layout="centered")

# ----------- CSS STYLE -----------
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap');

body, html, .stApp {
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(to right, #eef2f3, #dfe9f3);
    padding: 2rem;
}

h1 {
    text-align: center;
    font-weight: 700;
    color: #1a1a40;
    margin-bottom: 2rem;
}

.stTextInput>div>div>input,
.stFileUploader>div>div {
    border-radius: 8px;
    border: 1px solid #ccc !important;
    padding: 10px !important;
    font-size: 1rem !important;
    color: #2d2d2d;
    background-color: white;
}

.stTextInput label, .stFileUploader label {
    color: #333 !important;
    font-weight: 500;
}

.stButton>button {
    background: linear-gradient(to right, #4f46e5, #6366f1);
    border: none;
    color: white;
    font-size: 16px;
    padding: 0.7rem 1.5rem;
    border-radius: 10px;
    transition: background 0.3s ease;
    font-weight: 600;
}

.stButton>button:hover {
    background: linear-gradient(to right, #4338ca, #4f46e5);
}

.result-box {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(15px);
    padding: 2rem;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    margin-top: 2rem;
    color: #2d2d2d;
}

.result-box h2 {
    color: #3b82f6;
    font-weight: 700;
    font-size: 26px;
}

.result-box h4 {
    color: #6b7280;
    font-weight: 600;
    font-size: 20px;
    margin-top: 0.5rem;
}

.result-box p {
    font-size: 16px;
    color: #2d2d2d;
    line-height: 1.7;
}

.result-box ul li {
    margin-bottom: 8px;
    color: #374151;
}
</style>
"""

st.markdown(css, unsafe_allow_html=True)

# ----------- Title -----------
st.title("AI Resume Analyzer")

# ----------- AI Functions -----------
def extract_resume_data(base64_resume: str) -> dict:
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract Name, Email, Phone, Skills, Education, and Experience from this resume image. Reply ONLY in valid JSON format."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_resume}"
                    }
                }
            ]
        }
    ]
    response = completion(model=GEMINI_MODEL, messages=prompt, max_tokens=2048)
    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except:
        fixed = content.split("```json")[-1].split("```")[0].strip() if "```json" in content else content
        return json.loads(fixed)

def ats_score_with_improvements(resume_data: dict, job_title: str) -> dict:
    name = resume_data.get("Name", "The candidate")
    prompt = f"""
You are a professional AI Resume Evaluator. Given this resume data:

{json.dumps(resume_data)}

And the target job title: "{job_title}"

Your task:
1. Give an ATS score (out of 100).
2. Categorize the resume as Good (75+), Average (50-74), or Poor (<50).
3. Write personalized remarks using the name "{name}".
4. Suggest ways to improve their resume — specific and clear.

Respond in this format:
{{
  "score": <number>,
  "level": "<Good|Average|Poor>",
  "remarks": "<Your overall opinion using the candidate’s name>",
  "improvements": ["suggestion 1", "suggestion 2", ...]
}}
"""
    response = completion(model=GEMINI_MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=2048)
    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except:
        fixed = content.split("```json")[-1].split("```")[0].strip() if "```json" in content else content
        return json.loads(fixed)

# ----------- UI Inputs -----------
uploaded_file = st.file_uploader("Upload your resume (JPG or PNG only)", type=["jpg", "jpeg", "png"])
job_title = st.text_input("What job are you searching for?")
submit = st.button("Analyze Resume")

# ----------- Resume Analyzer Logic -----------
if submit:
    if not uploaded_file or not job_title.strip():
        st.warning("Please upload a resume and enter a job title.")
    else:
        encoded = base64.b64encode(uploaded_file.read()).decode("utf-8")
        with st.spinner("Analyzing resume..."):
            try:
                resume_data = extract_resume_data(encoded)
                results = ats_score_with_improvements(resume_data, job_title)

                st.markdown(f"""
                <div class="result-box">
                    <h2>Score: {results['score']} / 100</h2>
                    <h4>Level: {results['level']}</h4>
                    <p><strong>Remarks:</strong> {results['remarks']}</p>
                    <p><strong>Suggestions to Improve:</strong></p>
                    <ul>
                        {''.join([f"<li>{item}</li>" for item in results['improvements']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")
