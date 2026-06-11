# ...existing code...
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import os
from openai import AzureOpenAI
# ...existing code...

# Add dotenv support and load .env (optional)
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
# ...existing code...

# Read credentials (allow either API key or AD token)
api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_AD_TOKEN")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
deployment = os.getenv("DEPLOYMENT_NAME")

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

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # Render template via the Jinja2 environment to avoid passing the context into get_template()
    template = templates.env.get_template("index.html")
    content = template.render(request=request)
    return HTMLResponse(content)


@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # support both { "message": "..." } and OpenAI-like {"messages":[{role:..., content:...}]}
    user_input = None
    if isinstance(data, dict):
        if "message" in data:
            user_input = data["message"]
        elif "user_input" in data:
            user_input = data["user_input"]
        elif "messages" in data and isinstance(data["messages"], list) and len(data["messages"]) > 0:
            for m in reversed(data["messages"]):
                if m.get("role") == "user" and "content" in m:
                    user_input = m["content"]
                    break
            if user_input is None:
                user_input = data["messages"][0].get("content")

    if not user_input:
        raise HTTPException(status_code=400, detail="Missing 'message' in request body")

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": user_input}
        ]
    )

    return {"response": response.choices[0].message.content}
# ...existing code...
