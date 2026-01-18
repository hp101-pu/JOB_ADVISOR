import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

_client = None


def get_openai_client() -> Groq:
    global _client

    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            masked = f"{api_key[:4]}...{api_key[-4:]}"
            print(masked)
        else:
            raise RuntimeError("GROQ_API_KEY not set")

        _client = Groq(api_key=api_key)

    return _client


def get_openai_model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# import os
# from openai import OpenAI
# from dotenv import load_dotenv
# from pathlib import Path


# env_path=Path(__file__).resolve().parents[2]/".env"
# load_dotenv(dotenv_path=env_path)

# _client=None


# def get_openai_client() -> OpenAI:
#     global _client

#     if _client is None:
#         api_key = os.getenv("OPENAI_API_KEY")
#         if api_key:
#             masked=f"{api_key[:4]}...{api_key[-4:]}"
#             print(masked)
#         else:
#             raise RuntimeError("OPENAI_API_KEY not set")

#         _client = OpenAI(api_key=api_key)

#     return _client


# def get_openai_model() -> str:
#     return os.getenv("OPENAI_MODEL", "gpt-4o-mini")



