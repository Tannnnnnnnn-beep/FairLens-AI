import io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import os
from ml_analyzer import BiasAnalyzer
from mock_data_generator import generate_mock_data

app = FastAPI(title="FairLens AI Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = BiasAnalyzer()

@app.get("/")
def read_root():
    return {"message": "Welcome to FairLens AI API"}

@app.get("/api/mock-data")
def get_mock_data():
    """Generates mock data on the fly and returns it."""
    generate_mock_data(num_samples=1000, output_path="mock_hiring_data.csv")
    return {"message": "Mock data generated at mock_hiring_data.csv"}

@app.post("/api/audit")
async def audit_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        
        # Verify required columns minimum
        required = {'gender', 'college_tier', 'skills_score', 'projects', 'test_score', 'decision'}
        if not required.issubset(set(df.columns)):
            missing = required - set(df.columns)
            raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")
            
        results = analyzer.run_audit(df)
        return results
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# 🔐 Configure Gemini
# =========================
api_key = os.environ.get("GEMINI_API_KEY","AIzaSyA4U24AbOnEYlQshXnqAdGHjFbMfOA3loc")

if api_key == "DUMMY_KEY_MISSING":
    print("⚠️ WARNING: GEMINI_API_KEY is not set. The /api/coach endpoint will fail until you provide a real key.")

genai.configure(api_key=api_key)


class CoachMessage(BaseModel):
    role: str
    parts: str

class CoachRequest(BaseModel):
    message: str = ""
    language: str = "English"
    history: List[CoachMessage] = []


@app.post("/api/coach")
async def career_coach(request: CoachRequest):
    try:
        system_instruction = """
You are an AI Career Strategist and Decision Coach. 

FORMATTING & STYLE RULES:
- BE HIGHLY VISUAL AND ENGAGING: Use emojis heavily (🧠, 🚨, 💻, 👉, ✔, ❌, 🚀, 🎯) to break up text.
- Use bolding (**text**) for emphasis and headers.
- Never write walls of text. Use short, punchy lines.
- Structure your advice exactly like a top-tier career coach breaking down complex paths into easy choices.

WHEN ANSWERING CAREER PATH OR SKILL QUESTIONS, ALWAYS USE THIS STRUCTURE:

🧠 What’s Actually Going On
- Give a 1-2 sentence hard truth about the industry or their question.

🚨 Major Paths / Options
- Break down the options. For each option use:
  👉 Roles: (List roles)
  👉 Skills: (List skills)
  👉 Best if: (✔ You like...)
  📺 Recommended YouTube: (Provide a specific channel and a direct YouTube search link like https://www.youtube.com/results?search_query=topic)
  🏢 Where to Apply: (MUST suggest specific job portals like LinkedIn, Naukri.com, WorkIndia, Wellfound, OR Indian Government sites/schemes like National Career Service). Provide clickable links (e.g., https://www.naukri.com).

🛠 What You Should Do Next (HOW TO SOLVE THE PROBLEMS)
- DO NOT just point out problems. Give EXACT SOLUTIONS on how to fix them.
- Step 1: Immediate action to take.
- Step 2: Build 2-3 STRONG projects (Give exact, non-basic examples).
- Step 3: Add proof (GitHub, Portfolio, etc.)

✨ Personalized Strategy
- Give them a specific recommendation based on what they've told you.

🎤 Mock Interview Mode (If they ask for interview prep)
- Generate 3-5 REAL, most frequently asked interview questions from top companies (Google, Microsoft, Goldman Sachs, SBI, Wells Fargo, etc.) tailored to their target role.
- Include a mix of technical, behavioral, and situational questions.
- For each question, provide a quick tip on exactly how to answer it (e.g., using the STAR method).

🎯 Career Tip
- One piece of advice most people miss.

SPECIAL FAIRLENS FEATURES (Integrate when relevant):
- AGE & SECOND-CAREER AWARENESS: If the user is older, retired, or transitioning from careers like the Army, Sports, or Arts, provide highly specific second-career options. (e.g., Corporate Security/Operations for Army veterans; Sports Management/Coaching for Athletes; Creative Consulting/Teaching for Artists).
- BIAS BENCHMARKING: Compare their resume with top resumes and industry averages.
- FRAUD DETECTION: Detect and gently call out fake claims or overused buzzwords.
"""
        
        language_instruction = f"IMPORTANT: You MUST reply to the user entirely and exclusively in {request.language}. Translate ALL structural headings, labels (like 'Roles', 'Skills', 'Best if'), and bullet points into {request.language}." if request.language != "English" else ""
        tone_rule = "TONE RULE: If the user appears to be Gen Z or uses slang, adapt your tone to be highly friendly and use Gen Z slang (like 'W', 'no cap', 'fr', 'bet') BUT still provide the EXACT structured points and links. Otherwise, default to a highly PROFESSIONAL and FORMAL tone."
        context_prompt = f"{language_instruction}\n{tone_rule}\n\nUser Message: {request.message}"

        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=system_instruction
        )
        
        # Format history for Gemini
        formatted_history = []
        for msg in request.history:
            formatted_history.append({
                "role": msg.role,
                "parts": msg.parts
            })
            
        chat = model.start_chat(history=formatted_history)
        
        response = chat.send_message(
            context_prompt,
            stream=True,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1500,
            }
        )
        
        async def stream_generator():
            import asyncio
            
            # Simulated Thinking Process
            yield "Thinking... 🧠\n\n"
            await asyncio.sleep(0.6)
            yield "Analyzing your profile and query... 🔍\n\n"
            await asyncio.sleep(0.6)
            yield "Generating strategic roadmap... 🚀\n\n"
            await asyncio.sleep(0.5)
            yield "-----------------------------------\n\n"
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text

        return StreamingResponse(stream_generator(), media_type="text/plain")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))