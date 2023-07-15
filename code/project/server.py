from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from threading import Thread
import importlib
from . import cam

@asynccontextmanager
async def lifespan(app):
    print("Starting")
    cam_workers = []
    for idx in cam.enabled_cams:
        t = Thread(target=cam.motionDetection, args=(idx,))
        t.start()
        cam_workers.append(t)
    yield
    print("Shutdown")
    for i in range(len(cam.enabled_cams)):
        cam.stop_worker[i] = True
    for t in cam_workers:
        t.join()
    importlib.reload(cam)

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}

def main():
    uvicorn.run("project.server:app", host="0.0.0.0", port=8000, log_level="info", reload=True, workers=4)

if __name__ == "__main__":
    main()