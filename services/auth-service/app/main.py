from fastapi import FastAPI

app = FastAPI(
    title="Project Atlas - Identity Service",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Auth Service Running"
    }