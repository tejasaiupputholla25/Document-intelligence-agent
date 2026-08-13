import os

from dotenv import load_dotenv


load_dotenv()


HF_TOKEN = os.getenv("HF_TOKEN")
SERPERDEV_API_KEY = os.getenv("SERPERDEV_API_KEY")