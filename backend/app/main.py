from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ai as ai_router

app = FastAPI(title="Mentora AI")

# Lets the React (Vite) frontend call the API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router.router)


@app.get("/")
def root():
    return {"message": "Mentora AI backend is running"}