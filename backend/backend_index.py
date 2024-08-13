from fastapi import FastAPI
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
    context: str


# API endpoint to get a question by index
@app.get("/question/{index}")
def get_question(index: int):
    if index < len(interview_questions):
        return {"question": interview_questions[index]}
    return {"error": "Index out of range"}, 404


# API endpoint to generate feedback
@app.post("/generate_feedback")
def generate_feedback(request: FeedbackRequest):
    prompt = f"You are an interview assistant. The user answered: '{request.user_input}'. Provide feedback based on this answer. Context: {request.context}"
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
