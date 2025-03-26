from fastapi import FastAPI, WebSocket
import subprocess
import os
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI()

# Allow all origins (for testing, update as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL like ["https://your-frontend.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a directory for downloads
DOWNLOAD_PATH = "downloads/"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Home route (for health check)
@app.get("/")
def home():
    return {"message": "YouTube Downloader API is running!"}

# WebSocket route for downloading
@app.websocket("/ws/download")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        # Receive data from frontend
        data = await websocket.receive_json()
        url = data["url"]
        format = data["format"]
        resolution = data.get("resolution", "best")

        # Set output template for downloaded files
        output_template = f"{DOWNLOAD_PATH}%(title)s.%(ext)s"

        # Build the command for yt-dlp based on format
        if format == "mp3":
            command = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", output_template, url]
        else:
            command = ["yt-dlp", f"-f {resolution}+bestaudio", "-o", output_template, url]

        # Start the download process
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Monitor and send progress updates to frontend
        for line in process.stdout:
            await websocket.send_json({"progress": line.strip()})

        process.wait()  # Wait for the process to finish
        await websocket.send_json({"message": "Download complete!"})

    except Exception as e:
        await websocket.send_json({"error": str(e)})
        print(f"Error during download: {e}")
    
    finally:
        await websocket.close()  # Close WebSocket after completion
