from fastapi import FastAPI

app = FastAPI(title="Khmer AI Customer Assistant")


@app.get("/health")
def health():
    return {"status": "ok"}
