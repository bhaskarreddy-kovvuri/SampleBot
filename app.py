# ...existing code...
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

import os
import openai
from openai import AzureOpenAI
from pathlib import Path
# ...existing code...

# Add dotenv support and load .env (optional)
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

class Message(BaseModel):
    message: str

templates = Jinja2Templates(directory="templates")
# ...existing code...

# Read credentials (allow either API key or AD token)
api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_AD_TOKEN")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
deployment = os.getenv("DEPLOYMENT_NAME")

# Basic runtime info (do NOT print API keys)
print("Starting app — AZURE_OPENAI_ENDPOINT =", azure_endpoint)
print("Starting app — DEPLOYMENT_NAME =", deployment)

if not api_key and not os.getenv("AZURE_OPENAI_AD_TOKEN"):
    raise RuntimeError(
        "Missing Azure OpenAI credentials. Set AZURE_OPENAI_API_KEY or AZURE_OPENAI_AD_TOKEN."
    )
if not azure_endpoint:
    raise RuntimeError("Missing AZURE_OPENAI_ENDPOINT environment variable.")
if not deployment:
    raise RuntimeError("Missing DEPLOYMENT_NAME environment variable.")

# Pass the api_key explicitly to the client
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint,
)
# ...existing code...

@app.post("/chat")
async def chat(payload: Message = Body(...)):
    user_input = payload.message

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": user_input}
            ]
        )
    except openai.NotFoundError as e:
        # Clear, actionable error returned to the frontend/dev
        raise HTTPException(
            status_code=404,
            detail=(
                "Deployment not found. Verify DEPLOYMENT_NAME exactly matches a deployment in your Azure OpenAI resource "
                "and AZURE_OPENAI_ENDPOINT points to that resource. "
                "Check Azure Portal > your OpenAI resource > Deployments. SDK message: " + str(e)
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="OpenAI request failed: " + str(e))

    # Return 'reply' so the frontend (index.html) finds it via data.reply (or data.response)
    return {"reply": response.choices[0].message.content}
# ...existing code...
