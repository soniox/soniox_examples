import os
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

load_dotenv()

templates = Jinja2Templates(directory="templates")

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/temporary-api-key", response_class=JSONResponse)
async def get_temporary_api_key():
    try:
        response = requests.post(
            "https://api.soniox.com/v1/auth/temporary-api-key",
            headers={
                "Authorization": f"Bearer {os.getenv('SONIOX_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "usage_type": "transcribe_websocket",
                "expires_in_seconds": 60,
            },
        )

        if not response.ok:
            raise Exception(f"Error: {response.json()}")

        temporaryApiKeyData = response.json()
        return temporaryApiKeyData
    except Exception as error:
        print(error)
        return JSONResponse(
            status_code=500,
            content={"error": "Server failed to obtain temporary api key."},
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    uvicorn.run(app, host="0.0.0.0", port=port)
