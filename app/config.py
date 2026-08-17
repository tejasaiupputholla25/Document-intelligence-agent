import os

from dotenv import load_dotenv


load_dotenv()


HF_TOKEN = os.getenv("HF_TOKEN")
SERPERDEV_API_KEY = os.getenv("SERPERDEV_API_KEY")


if not HF_TOKEN:
    raise ValueError(
        "HF_TOKEN is missing. "
        "Add HF_TOKEN to your .env file."
    )