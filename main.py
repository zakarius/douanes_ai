
from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_swagger_ui_html,
)
import uvicorn

# APi class
from routers import V1, V2

app = FastAPI(
    title="SuperDouanier API",
    version="1.2.0",
)


app.include_router(V2, prefix="/v2", tags=["V2"])
app.include_router(V1, prefix="", tags=["V1"], deprecated=True)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
