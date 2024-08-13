import streamlit as st
import requests
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import numpy as np
import pydub
import io

API_URL = "http://localhost:8000"

# Initialize session state variables
if "mode" not in st.session_state:
    st.session_state.mode = "ask"  # "ask" or "feedback"
    st.session_state.user_response = ""
    st.session_state.history = []


# Callback function to handle user input
def handle_input():
    st.session_state.user_response = st.session_state.temp_response
    st.session_state.mode = "feedback"


# Function to get the next question from backend API
def get_next_question():
    response = requests.get(f"{API_URL}/next_question")
    if response.status_code == 200:
        data = response.json()
        return data["question"], data["completed"]
    return None, True


# Function to generate feedback via backend API
def generate_feedback(user_input, context):
    response = requests.post(
        f"{API_URL}/generate_feedback",
        json={"user_input": user_input},
        params={"context": context},
    )
    if response.status_code == 200:
        return response.json()["feedback"]
    return "Error generating feedback."


# Audio processor class for handling voice input
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = []

    def recv(self, frame):
        audio_frame = frame.to_ndarray()
        self.audio_frames.append(audio_frame)
        return frame

    def get_audio_data(self):
        if self.audio_frames:
            audio = np.concatenate(self.audio_frames)
            self.audio_frames = []
            return audio
        return None


# Convert audio to text using OpenAI Whisper or other service
def convert_audio_to_text(audio_data):
    # Placeholder: Integrate your ASR service here (e.g., OpenAI Whisper)
    # For now, we'll just return a dummy text.
    return "This is a dummy transcription of your voice."


# Streamlit app
def main():
    st.title("JavaScript Virtual Interview Assistant")

    st.write(
        """
        Welcome to the JavaScript Virtual Interview Assistant!
        Answer the interview questions, and I'll provide feedback on your answers.
        """
    )

    # Display previous questions and feedback
    if st.session_state.history:
        st.write("### Previous Questions and Feedback")
        for i, entry in enumerate(st.session_state.history):
            st.write(f"**Question {i+1}:** {entry['question']}")
            st.write(f"**Your Answer:** {entry['answer']}")
            st.write(f"**Feedback:** {entry['feedback']}")
            st.write("---")

    if st.session_state.mode == "ask":
        # Ask the next interview question
        question, completed = get_next_question()
        if not completed:
            st.write(f"### Current Question")
            st.write(f"**Question:** {question}")

            st.text_input("Your answer:", key="temp_response", on_change=handle_input)

            # Voice input using WebRTC
            webrtc_ctx = webrtc_streamer(
                key="speech-to-text",
                mode=WebRtcMode.SENDRECV,
                audio_processor_factory=AudioProcessor,
                media_stream_constraints={"audio": True, "video": False},
            )

            if st.button("Submit Voice Response"):
                if webrtc_ctx.audio_processor:
                    audio_data = webrtc_ctx.audio_processor.get_audio_data()
                    if audio_data is not None:
                        # Convert audio data to a recognizable format
                        sound = pydub.AudioSegment(
                            audio_data.tobytes(),
                            frame_rate=16000,
                            sample_width=2,
                            channels=1,
                        )
                        buffer = io.BytesIO()
                        sound.export(buffer, format="wav")
                        audio_bytes = buffer.getvalue()

                        # Convert audio to text
                        transcription = convert_audio_to_text(audio_bytes)
                        st.session_state.temp_response = transcription
                        handle_input()
                else:
                    st.write("Please speak into the microphone.")

        else:
            st.write("You have completed the interview!")

    elif st.session_state.mode == "feedback":
        # Generate and display feedback
        last_question = (
            st.session_state.history[-1]["question"] if st.session_state.history else ""
        )
        feedback = generate_feedback(st.session_state.user_response, last_question)
        st.session_state.history.append(
            {
                "question": last_question,
                "answer": st.session_state.user_response,
                "feedback": feedback,
            }
        )

        st.write(f"**Feedback:** {feedback}")

        if st.button("Next Question"):
            st.session_state.mode = "ask"
            st.session_state.user_response = ""


if __name__ == "__main__":
    main()
