from main import AegisEngine
from dotenv import load_dotenv
import json

load_dotenv()


aegis = AegisEngine()
aegis.accept_query("What events do I have?")