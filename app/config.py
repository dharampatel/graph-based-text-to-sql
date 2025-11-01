import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash', api_key=os.getenv('GOOGLE_API_KEY'))
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")