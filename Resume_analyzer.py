import streamlit as st
import base64
import json
import os
from litellm import completion

# ---------------------- LOAD GEMINI API KEY ----------------------
api_key = st.secrets["GEMINI_API_KEY"]
os.environ["GEMINI_API_KEY"] = api_key

# Gemini model (text + image capable)
GEMINI_MODEL = "gemini/gemini-1.5-flash"

# ---------------------- EXTRACT RESUME DATA ----------------------
def extract_resume_data(base64_resume: str) -> dict:
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract the following information from this resume: Name, Email, Phone, Skills, Education, Experience."
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
    return json.loads(response.choices[0].message.content)

# ---------------------- EVALUATE ATS SCORE ----------------------
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
       - If Good: Praise the resume and recommend submitting.
       - If Average: Suggest some improvements.
       - If Poor: Point out major gaps and give clear improvement advice.

    Return your response in this JSON format:
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
    return json.loads(response.choices[0].message.content)

# ---------------------- STREAMLIT UI ----------------------
st.set_page_config(page_title="Resume Analyzer AI", layout="centered")
st.title("Resume Analyzer AI Agent")

st.markdown("Upload your resume (Only JPG, JPEG, or PNG formats are supported)")

uploaded_file = st.file_uploader("Upload Resume", type=["png", "jpg", "jpeg"])
job_description = st.text_area("Paste the job description here:", height=200)

if uploaded_file and job_description:
    bytes_data = uploaded_file.read()
    encoded_resume = base64.b64encode(bytes_data).decode("utf-8")

    with st.spinner("Extracting resume data..."):
        try:
            resume_data = extract_resume_data(encoded_resume)
            st.subheader("Extracted Resume Information")
            st.json(resume_data)
        except Exception as e:
            st.error(f"Failed to extract resume data:\n{e}")

    with st.spinner("Evaluating resume against job description..."):
        try:
            ats_result = evaluate_ats_score(resume_data, job_description)
            st.subheader("ATS Evaluation Result")
            st.write(f"**ATS Score:** {ats_result['score']} / 100")
            st.write(f"**Level:** {ats_result['level']}")
            st.write(f"**Remarks:** {ats_result['remarks']}")
        except Exception as e:
            st.error(f"Failed to evaluate resume:\n{e}")

st.markdown("---")
st.markdown("Built using Gemini and Streamlit.")
