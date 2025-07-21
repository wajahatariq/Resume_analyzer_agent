import streamlit as st
import base64
import json
import os
from litellm import completion

# ---------------------- CONFIG ----------------------
api_key = st.secrets["GEMINI_API_KEY"]
os.environ["GEMINI_API_KEY"] = api_key
GEMINI_MODEL = "gemini/gemini-1.5-flash"

st.set_page_config(page_title="AI Resume Analyzer", layout="centered")

# ---------------------- CSS ----------------------
custom_css = """
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        background: linear-gradient(to right, #f5f7fa, #c3cfe2);
    }
    .stApp {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
    }
    h1 {
        text-align: center;
        color: #1f2937;
        margin-bottom: 2rem;
    }
    .stFileUploader, .stTextInput, .stButton {
        padding: 0.5rem !important;
    }
    .stButton button {
        background-color: #2563eb !important;
        color: white !important;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
    }
    .stButton button:hover {
        background-color: #1d4ed8 !important;
    }
    .result-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }
    .score {
        font-size: 2rem;
        font-weight: bold;
        color: #1e40af;
    }
    .level {
        font-size: 1.2rem;
        font-weight: 500;
        color: #374151;
    }
    .remarks {
        margin-top: 1rem;
        font-style: italic;
        color: #4b5563;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------- Title ----------------------
st.title("AI Resume Analyzer")

# ---------------------- Functions ----------------------
def extract_resume_data(base64_resume: str) -> dict:
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract the following from this resume image: Name, Email, Phone, Skills, Education, Experience. Respond only in valid JSON."
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
    response = completion(
        model=GEMINI_MODEL,
        messages=prompt,
        max_tokens=2048
    )
    content = response.choices[0].message.content.strip()
    try:
        if content.endswith("}"):
            return json.loads(content)
        else:
            fixed = content.split("```json")[-1].split("```")[0].strip() if "```json" in content else content
            return json.loads(fixed)
    except Exception as e:
        raise ValueError("Gemini returned invalid JSON:\n\n" + content)

def evaluate_ats_score(resume_data: dict, job_title: str) -> dict:
    prompt = f"""
    You are an ATS evaluator AI. Given the following resume data:

    {json.dumps(resume_data, indent=2)}

    And the job title the user is targeting:
    {job_title}

    Do the following:
    1. Score the resume out of 100 based on relevance to the job title.
    2. Classify it as: 'Good' (75+), 'Average' (50-74), 'Poor' (<50).
    3. Write a personalized remark.

    Respond only in this format:
    {{
      "score": <number>,
      "level": "<Good|Average|Poor>",
      "remarks": "<Your AI-generated feedback>"
    }}
    """
    response = completion(
        model=GEMINI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )
    content = response.choices[0].message.content.strip()
    try:
        fixed = content.split("```json")[-1].split("```")[0].strip() if "```json" in content else content
        return json.loads(fixed)
    except Exception as e:
        raise ValueError("Gemini returned invalid JSON:\n\n" + content)

# ---------------------- UI ----------------------
uploaded_file = st.file_uploader("Upload Your Resume (JPG or PNG only)", type=["jpg", "jpeg", "png"])
job_title = st.text_input("What job are you searching for?")
submit = st.button("Analyze My Resume")

# ---------------------- Execution ----------------------
if submit:
    if not uploaded_file:
        st.warning("Please upload a resume image file.")
    elif not job_title.strip():
        st.warning("Please enter the job you’re targeting.")
    else:
        bytes_data = uploaded_file.read()
        encoded_resume = base64.b64encode(bytes_data).decode("utf-8")

        with st.spinner("Extracting resume and evaluating..."):
            try:
                resume_data = extract_resume_data(encoded_resume)
                ats_result = evaluate_ats_score(resume_data, job_title)

                score = ats_result['score']
                level = ats_result['level']
                remarks = ats_result['remarks']

                st.markdown(f"""
                    <div class="result-container">
                        <div class="score">Score: {score} / 100</div>
                        <div class="level">Level: {level}</div>
                        <div class="remarks">"{remarks}"</div>
                    </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")
