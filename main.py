from fastapi import FastAPI, WebSocket
import subprocess
import os

app = FastAPI()

DOWNLOAD_PATH = "downloads/"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

@app.get("/")
def home():
    return {"message": "YouTube Downloader API is running!"}

@app.websocket("/ws/download")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_json()
    url = data["url"]
    format = data["format"]
    resolution = data.get("resolution", "best")

    output_template = f"{DOWNLOAD_PATH}%(title)s.%(ext)s"

    if format == "mp3":
        command = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", output_template, url]
    else:
        command = ["yt-dlp", f"-f {resolution}+bestaudio", "-o", output_template, url]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    for line in process.stdout:
        await websocket.send_json({"progress": line.strip()})

    process.wait()
    await websocket.send_json({"message": "Download complete!"})
    await websocket.close()
