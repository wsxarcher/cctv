from contextlib import asynccontextmanager

import os
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import websockets
from fastapi import Depends, FastAPI, Request, Response, Form, Cookie, Header
import uvicorn
from threading import Thread
from multiprocessing import Queue
import importlib
from fastapi.responses import StreamingResponse, RedirectResponse, FileResponse
from fastapi import HTTPException
import uuid
from . import database
from . import schema
from . import cam
from . import db_logic

TMP_STREAMING = os.environ.get("TMP_STREAMING")


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

db_logic.create_user("admin", "password")
db_logic.create_user("guest", "password")
# db_logic.logout_everywhere("admin")


def get_logged_user(token: str | None = Cookie(default=None)):
    if user := db_logic.is_logged(token):
        return user
    else:
        return None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("template.html", {"request": request})


@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request, token: str | None = Cookie(default=None)):
    db_logic.logout(token)
    response = templates.TemplateResponse("login.html", {"request": request})
    response.headers["HX-Trigger"] = "loggedout"
    return response


@app.delete("/session", response_class=HTMLResponse)
async def session_delete(request: Request, token: str = Form()):
    db_logic.logout(token)
    response = templates.TemplateResponse("login.html", {"request": request})
    response.headers["HX-Trigger"] = "loggedout"
    return Response(content="")


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    user_agent: str | None = Header(default=None),
):
    response = templates.TemplateResponse("login.html", {"request": request})
    if token := db_logic.login(username, password, user_agent, request.client.host):
        response.set_cookie(key="token", value=token, httponly=True)
        response.headers["HX-Trigger"] = "loggedin"
    else:
        return HTMLResponse(content="Wrong login details", status_code=401)
    return response


@app.get("/alerts", response_class=HTMLResponse)
async def alerts(request: Request, user=Depends(get_logged_user)):
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("alerts.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def settings(
    request: Request,
    user=Depends(get_logged_user),
    token: str | None = Cookie(default=None),
):
    if not user:
        return RedirectResponse("/login")
    sessions_db = db_logic.sessions(user)
    sessions = []
    for session_db in sessions_db:
        sessions.append(
            {
                "token": session_db.token,
                "user_agent": session_db.user_agent,
                "ip": session_db.ip,
            }
        )
    sessions.insert(
        0, sessions.pop(list(map(lambda s: s["token"] == token, sessions)).index(True))
    )
    return templates.TemplateResponse(
        "settings.html", {"request": request, "sessions": sessions, "username": user.username }
    )


@app.get("/cams", response_class=HTMLResponse)
async def cams(request: Request, user=Depends(get_logged_user)):
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "cams.html", {"request": request, "number": cam.number_of_cams}
    )


@app.get("/streaming/{i}.m3u8")
async def streaming_playlist(i: int, request: Request, user=Depends(get_logged_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not logged it")
    path = TMP_STREAMING + "/" + str(i) + ".m3u8"
    base_url = str(request.base_url)
    # ngrok https is transparent
    if "ngrok" in base_url or "devtunnels" in base_url:
        base_url = base_url.replace("http://", "https://")
    print(base_url)
    with open(path, "r") as f:
        content = f.read()
        content = content.replace(cam.SEGMENTS_URL, base_url + "streaming")
        return Response(content=content, media_type="application/vnd")


@app.get("/streaming/{fragment}")
async def streaming_fragment(
    fragment: str, request: Request, user=Depends(get_logged_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not logged it")
    file_path = os.path.join(TMP_STREAMING, os.path.basename(fragment))
    return FileResponse(file_path)


@app.get("/cam/{i}")
async def stream(
    i: int, user=Depends(get_logged_user), token: str | None = Cookie(default=None)
):
    if not user:
        raise HTTPException(status_code=401, detail="Wrong login details")
    if i >= cam.number_of_cams:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
        )
    watcher_id = uuid.uuid4()
    print("added watcher {} to cam {}".format(watcher_id, i))
    check_session = lambda token=token: get_logged_user(token)
    return StreamingResponse(
        cam.streamer(i, watcher_id, check_session),
        media_type="multipart/x-mixed-replace;boundary=frame",
    )


def main():
    workers = os.environ.get("WORKERS", 4)
    if os.environ.get("DEBUG") == "1":
        reload = True
    else:
        reload = False
    uvicorn.run(
        "project.server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=reload,
        workers=workers,
    )


if __name__ == "__main__":
    main()
