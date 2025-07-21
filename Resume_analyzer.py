import streamlit as st
import base64
import json
import os
from litellm import completion
from typing import Dict

# ---------------------- LOAD GEMINI API KEY ----------------------
api_key = os.getenv("GEMINI_API_KEY")
os.environ["GEMINI_API_KEY"] = api_key

MODEL_FLASH = "gemini/gemini-1.5-flash"
MODEL_VISION = "gemini/gemini-pro-vision"

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
        model=MODEL_VISION,
        messages=prompt,
        max_tokens=2048
    )
    return json.loads(response.choices[0].message.content)

# ---------------------- EVALUATE ATS SCORE ----------------------
def evaluate_ats_score(resume_data: dict, job_description: str) -> dict:
    prompt = f"""
    Given the following resume data:
    {json.dumps(resume_data, indent=2)}

    And this job description:
    {job_description}

    Evaluate the resume using an ATS system and return:
    - ATS Score (out of 100)
    - What improvements can be made to better match the job description?
    """
    response = completion(
        model=MODEL_FLASH,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )
    return json.loads(response.choices[0].message.content)

# ---------------------- STREAMLIT UI ----------------------
st.set_page_config(page_title="Resume Analyzer AI", layout="centered")
st.title("📄 Resume Analyzer AI Agent")

uploaded_file = st.file_uploader("Upload your resume (Image - PNG/JPG only)", type=["png", "jpg", "jpeg"])
job_description = st.text_area("Paste the job description here:", height=200)

if uploaded_file and job_description:
    bytes_data = uploaded_file.read()
    encoded_resume = base64.b64encode(bytes_data).decode("utf-8")

    with st.spinner("🔍 Extracting resume data..."):
        try:
            resume_data = extract_resume_data(encoded_resume)
            st.subheader("✅ Extracted Resume Info")
            st.json(resume_data)
        except Exception as e:
            st.error(f"Failed to extract resume data: {e}")

    with st.spinner("📊 Evaluating resume with ATS..."):
        try:
            ats_result = evaluate_ats_score(resume_data, job_description)
            st.subheader("📋 ATS Evaluation")
            st.json(ats_result)
        except Exception as e:
            st.error(f"Failed to evaluate ATS: {e}")

st.markdown("---")
st.markdown("🚀 Made with Gemini, LiteLLM, and Streamlit")
