from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

# Load configuration and environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI app
app = FastAPI()

# List of interview questions
interview_questions = [
    "What is JavaScript and how is it used in web development?",
    "Can you explain the difference between var, let, and const in JavaScript?",
    "What are closures in JavaScript and how do they work?",
    "How does prototypal inheritance work in JavaScript?",
    "Can you explain event delegation in JavaScript?",
]


# Define the input model for feedback generation
class FeedbackRequest(BaseModel):
    user_input: str


# API endpoint to get the next question
@app.get("/next_question")
def next_question(request: Request):
    print("***************")
    print("request", request)
    print("State", request.state)
    session = request.state.session
    question_index = session.get("question_index", 0)

    if question_index >= len(interview_questions):
        return {"message": "Interview completed", "completed": True}

    question = interview_questions[question_index]
    session["question_index"] = question_index + 1
    request.state.session = session

    return {"question": question, "completed": False}


# API endpoint to generate feedback
@app.post("/generate_feedback")
def generate_feedback(request: FeedbackRequest, context: str = None):
    prompt = f"You are an interview assistant. The user answered: '{request.user_input}'. Provide feedback based on this answer. Context: {context}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant providing feedback for interview answers.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return {"feedback": response.choices[0].message["content"].strip()}
