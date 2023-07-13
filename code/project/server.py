from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

def main():
    uvicorn.run("project.server:app", host="0.0.0.0", port=8000, log_level="info", reload=True, workers=4)

if __name__ == "__main__":
    main()