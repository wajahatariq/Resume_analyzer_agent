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
