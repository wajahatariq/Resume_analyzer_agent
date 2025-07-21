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

st.title("Resume Analyzer AI Agent")
st.markdown("Upload your resume image (JPG/PNG) and paste a job description. The AI will extract resume data and analyze it using ATS logic.")

# ---------------------- FUNCTIONS ----------------------
def extract_resume_data(base64_resume: str) -> dict:
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract the following information from this resume: Name, Email, Phone, Skills, Education, Experience. Respond only in valid JSON format."
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

    # Ensure JSON is valid before parsing
    try:
        # Try to close the JSON if Gemini left it open
        if content.endswith("}"):
            return json.loads(content)
        else:
            fixed = content.split("```json")[-1].split("```")[0].strip() if "```json" in content else content
            return json.loads(fixed)
    except Exception as e:
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
        fixed = content.split("```json")[-1].split("```")[0].strip() if "```json" in content else content
        return json.loads(fixed)
    except Exception as e:
        raise ValueError("Gemini returned invalid JSON:\n\n" + content)

# ---------------------- UI ----------------------
uploaded_file = st.file_uploader("Upload Resume Image", type=["jpg", "jpeg", "png"])
job_description = st.text_area("Paste Job Description", height=200)
submit = st.button("Submit")

if submit:
    if not uploaded_file:
        st.warning("Please upload a JPG or PNG resume.")
    elif not job_description.strip():
        st.warning("Please paste a job description.")
    else:
        bytes_data = uploaded_file.read()
        encoded_resume = base64.b64encode(bytes_data).decode("utf-8")

        with st.spinner("Extracting resume data..."):
            try:
                resume_data = extract_resume_data(encoded_resume)
                st.subheader("Extracted Resume Information")
                st.json(resume_data)
            except Exception as e:
                st.error(f"Failed to extract resume data: {e}")
                st.stop()

        with st.spinner("Evaluating ATS score..."):
            try:
                ats_result = evaluate_ats_score(resume_data, job_description)
                score = ats_result['score']
                level = ats_result['level']
                remarks = ats_result['remarks']

                st.subheader("ATS Evaluation")
                st.markdown(f"**Score:** {score} / 100")
                st.markdown(f"**Level:** {level}")
                st.markdown(f"**Remarks:** {remarks}")

            except Exception as e:
                st.error(f"Failed to evaluate ATS score: {e}")
