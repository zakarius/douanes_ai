from fastapi import FastAPI
import uvicorn

# APi class
from routers import V1, V2, utils

app = FastAPI(
    title="SuperDouanier API",
    version="1.2.0",
)


app.include_router(V2, prefix="/v2", tags=["V2"])
app.include_router(V1, prefix="", tags=["V1"], deprecated=True)
app.include_router(utils.router, prefix="/utils", tags=["Utils"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
