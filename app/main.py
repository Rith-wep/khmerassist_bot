from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, knowledge

app = FastAPI(title="Khmer AI Customer Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(knowledge.router)


@app.get("/health")
def health():
    return {"status": "ok"}
