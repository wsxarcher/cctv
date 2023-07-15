from contextlib import asynccontextmanager

import websockets
from fastapi import FastAPI
import uvicorn
from threading import Thread
from multiprocessing import Queue
import importlib
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
import uuid
from . import cam

@asynccontextmanager
async def lifespan(app):
    print("Starting")
    cam_workers = []
    for i in range(len(cam.enabled_cams)):
        t = Thread(target=cam.motionDetection, args=(i,))
        t.start()
        cam_workers.append(t)
    yield
    print("Shutdown")
    cam.shutdown(cam_workers)
    importlib.reload(cam)

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/cams")
async def cams():
    return {"number": len(cam.enabled_cams)}

@app.get("/cam/{i}")
async def stream(i: int):
    if i >= len(cam.enabled_cams):
        raise HTTPException(
            status_code=404,
            detail="Item not found",
        )
    watcher_id = uuid.uuid4()
    print("added watcher {} to cam {}".format(watcher_id, i))
    return StreamingResponse(cam.streamer(i, watcher_id), media_type="multipart/x-mixed-replace;boundary=frame")

def main():
    uvicorn.run("project.server:app", host="0.0.0.0", port=8000, log_level="info", reload=True, workers=4)

if __name__ == "__main__":
    main()