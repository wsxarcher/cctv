from contextlib import asynccontextmanager

import os
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import websockets
from fastapi import FastAPI, Request
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
    for i in range(cam.number_of_cams):
        t = Thread(target=cam.motionDetection, args=(i,))
        t.start()
        cam_workers.append(t)
    yield
    print("Shutdown")
    cam.shutdown(cam_workers)
    importlib.reload(cam)

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("cams.html", { "request": request, "number": cam.number_of_cams })

@app.get("/number_cams")
async def cams():
    return {"number": cam.number_of_cams}

@app.get("/cam/{i}")
async def stream(i: int):
    if i >= cam.number_of_cams:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
        )
    watcher_id = uuid.uuid4()
    print("added watcher {} to cam {}".format(watcher_id, i))
    return StreamingResponse(cam.streamer(i, watcher_id), media_type="multipart/x-mixed-replace;boundary=frame")

def main():
    workers = os.environ.get("WORKERS", 4)
    if os.environ.get("DEBUG") == "1":
        reload = True
    else:
        reload = False
    uvicorn.run("project.server:app", host="0.0.0.0", port=8000, log_level="info", reload=reload, workers=workers)

if __name__ == "__main__":
    main()