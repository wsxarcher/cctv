from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from threading import Thread
import importlib
from . import cam

@asynccontextmanager
async def lifespan(app):
    print("Starting")
    t = Thread(target=cam.motionDetection)
    t.start()
    yield
    print("Shutdown")
    cam.stop_worker = True
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