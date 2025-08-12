from google import genai
from google.genai import types
import fitz as fz
import streamlit as st

client = genai.Client(api_key="""INSERT YOUR API KEY HERE, MIGHT UPDATE THIS FILE WITH AN ENV TO HIDE MY OWN KEY""")

def extract_text_from_pdf(file):
    """Extract text from a PDF file using PyMuPDF."""
    try:
        pdf_document = fz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in pdf_document:
            text += page.get_text() or ""
        pdf_document.close()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

class Agent:
    def __init__(self, client=client, system_instruct=""):
        self.client = client
        self.model_name = "gemini-2.5-flash"
        if "history" not in st.session_state:
            st.session_state.history = []
        self.history = st.session_state.history
        if system_instruct.strip() and not self.history:
            self.history.append(types.Content(role="user", parts=[types.Part(text=system_instruct)]))

    def __call__(self, prompt):
        self.history.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=self.history,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=-1)
            )
        )
        self.history.append(types.Content(role="model", parts=[types.Part(text=response.text)]))
        st.session_state.history = self.history
        return response.text

if "bot" not in st.session_state:
    st.session_state.bot = Agent(system_instruct=""" You are a helpful assistant, named PlotPal, for new and lost Artificial Intelligence/Data Science students trying to understand what to do in their assignments.
                                                        Help them with questions like which ML model to choose or which graph is best for some relationship.
                                                        Provide a reason as to why you chose this option and provide alternatives. 
                                                        If the user asks you to code something, first provide them a link to documentation of said relevant code. If they still ask you to do it, then give them the code but advise them that its better to learn with documentation than using you for code
                                                        Take in PDF files and parse through them to explain and suggest solutions as to what their assignment asks of them, or answer questions they have via text based prompts. Keep it short and simple.
                                                        Stay on track, do not answer questions unrelated to AI or Data Science. Do not explain PDFs that are unrelated.
                                                        Introduce yourself like this only the first time user enters a prompt: 'Hello! I'm PlotPal, your AI/Data Science assignment assistant.
                                                        I can help you with things like deciding which ML model to use, or which graph is most suitable for a relationship. To get started, upload a PDF or ask a question!' """)

def main():
    st.title("PlotPal")
    
    # Custom CSS styling 
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@700&display=swap');
        .user-message {
            background-color: #2c3132;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
            display: inline-block;
            max-width: 90%;
            color: #ffffff;
        }
        .bot-message {
            background-color: #ff7100;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
            display: inline-block;
            max-width: 90%;
            color: #ffffff;
        }
        .stTitle {
            font-family: "League Spartan", sans-serif;
            font-size: 2.5em;
            font-weight: 700;
            margin: 0;
            padding: 10px;
        }
        .stApp {
            background: #2c3132 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Display previous chat history
    for content in st.session_state.history:
        if content.role == "user" and content.parts[0].text != st.session_state.bot.history[0].parts[0].text:
            st.markdown(f'<div class="user-message">User: {content.parts[0].text}</div>', unsafe_allow_html=True)
        elif content.role == "model":
            st.markdown(f'<div class="bot-message">PlotPal: {content.parts[0].text}</div>', unsafe_allow_html=True)
    
    # File uploader
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"], key="pdf_uploader")
    
    # Text input
    user_input = st.text_input("Ask a question:", key="user_input")
    display_input = user_input
    # Process input when Enter is pressed or file is uploaded
    if st.session_state.get("user_input") and st.session_state.user_input.strip() and st.session_state.get("prev_input") != st.session_state.user_input.strip():
        current_input = st.session_state.user_input.strip() 
        combined_text = current_input
        if uploaded_file:
            pdf_text = extract_text_from_pdf(uploaded_file)
            if pdf_text:
                combined_text += "\n\n" + pdf_text  # Add PDF text internally for processing
        if combined_text:
            try:
                response = st.session_state.bot(combined_text)
                st.markdown(f'<div class="user-message">User: {display_input}</div>', unsafe_allow_html=True)  
                st.markdown(f'<div class="bot-message">PlotPal: {response}</div>', unsafe_allow_html=True)
                st.markdown('<script>window.scrollTo(0, document.body.scrollHeight);</script>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")
        st.session_state.prev_input = display_input

if __name__ == "__main__":  
    main()