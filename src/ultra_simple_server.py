"""
Servidor Ultra Simple - Garantizado que funciona
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Trading Server Running", "status": "OK"}

@app.get("/api/health")
async def health():
    return {"status": "OK", "version": "1.0.0"}

if __name__ == "__main__":
    print("=" * 60)
    print("TRADING SERVER STARTING")
    print("Server: http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)
