import os
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

load_dotenv()

templates = Jinja2Templates(directory="templates")

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    headers = {
        "Authorization": f"Bearer {os.getenv('SONIOX_API_KEY')}",
        "Content-Type": "application/json",
    }
    payload = {
        "usage_type": "transcribe_websocket",
        "expires_in_seconds": 300,  # 5 minutes, adjust to fit your needs
    }

    req = requests.post(
        "https://api.soniox.com/v1/auth/temporary-api-key",
        headers=headers,
        json=payload,
    )

    if req.ok:
        data = req.json()
        api_key = data.get("api_key", "")
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "api_key": api_key,
            },
        )
    else:
        print(f"Error: {req.status_code}, {req.text}")
        return templates.TemplateResponse(
            request=request,
            name="error.html",
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
