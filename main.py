from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# APi class
from routers import V1, V2, tools, V3

app = FastAPI(
    title="SuperDouanier API",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "douanes-togolaises.web.app'",
        "douanes-togolaises.firebaseapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

app.include_router(V3, prefix="/v3", tags=["v3"])
app.include_router(V2, prefix="/v2", tags=["v2"])
app.include_router(V1, prefix="", tags=["v1"], deprecated=True)
app.include_router(tools, prefix="/utils", tags=["Utils"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
