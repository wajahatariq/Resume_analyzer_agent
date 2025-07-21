import streamlit as st
import base64
import json
import os
from litellm import completion

# ---------------------- CONFIG ----------------------
api_key = st.secrets["GEMINI_API_KEY"]
os.environ["GEMINI_API_KEY"] = api_key
GEMINI_MODEL = "gemini/gemini-1.5-flash"

st.set_page_config(page_title="Resume Analyzer AI", layout="centered")

# ---------------------- CUSTOM CSS ----------------------
st.markdown("""
    <style>
        body {
            background-color: #f5f7fa;
        }
        .main {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .result-box {
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            font-size: 16px;
        }
        .good {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .average {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }
        .poor {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main'>", unsafe_allow_html=True)
st.title("📄 Resume Analyzer AI Agent")
st.markdown("Upload your resume image (JPG/PNG) and paste a job description. The AI will extract resume data and analyze it using ATS logic.")

# ---------------------- FUNCTIONS ----------------------
def extract_resume_data(base64_resume: str) -> dict:
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract the following information from this resume: Name, Email, Phone, Skills, Education, Experience.\n\nRespond only in pure JSON format."
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
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("Gemini returned invalid JSON:\n\n" + content)

def evaluate_ats_score(resume_data: dict, job_description: str) -> dict:
    prompt = f"""
    You are an ATS evaluator AI. Given the following resume data:

    {json.dumps(resume_data, indent=2)}

    And this job description:
    {job_description}

    Do the following:
    1. Give the ATS score out of 100.
    2. Classify the score as 'Good' (>=75), 'Average' (50-74), or 'Poor' (<50).
    3. Provide a short remark depending on the score.

    Respond only in JSON using this format:
    {{
      "score": <number>,
      "level": "<Good|Average|Poor>",
      "remarks": "<AI-generated remark>"
    }}
    """
    response = completion(
        model=GEMINI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )
    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("Gemini returned invalid JSON:\n\n" + content)

# ---------------------- UI ----------------------
uploaded_file = st.file_uploader("Upload Resume Image", type=["jpg", "jpeg", "png"])
job_description = st.text_area("Paste Job Description", height=200)
submit = st.button("Submit")

if submit:
    if not uploaded_file:
        st.warning("⚠️ Please upload a JPG or PNG resume.")
    elif not job_description.strip():
        st.warning("⚠️ Please paste a job description.")
    else:
        bytes_data = uploaded_file.read()
        encoded_resume = base64.b64encode(bytes_data).decode("utf-8")

        with st.spinner("🔍 Extracting resume data..."):
            try:
                resume_data = extract_resume_data(encoded_resume)
                st.subheader("Extracted Resume Information")
                st.json(resume_data)
            except Exception as e:
                st.error(f"❌ Failed to extract resume data:\n{e}")
                st.stop()

        with st.spinner("📊 Evaluating ATS score..."):
            try:
                ats_result = evaluate_ats_score(resume_data, job_description)
                score = ats_result['score']
                level = ats_result['level'].lower()
                remarks = ats_result['remarks']

                level_class = "good" if level == "good" else "average" if level == "average" else "poor"

                st.markdown(f"""
                    <div class="result-box {level_class}">
                        <strong>ATS Score:</strong> {score} / 100<br>
                        <strong>Level:</strong> {level.capitalize()}<br>
                        <strong>Remarks:</strong> {remarks}
                    </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Failed to evaluate ATS score:\n{e}")

st.markdown("</div>", unsafe_allow_html=True)
