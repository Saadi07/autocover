from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.event_router import event_router
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(event_router)

@app.get("/" ,tags=["health-check"])
def health_check():
    return {"message": "Server is up and running"}

# if __name__ == "__main__":
 
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# CMD ["gunicorn","-w","4","-k","uvicorn.workers.UvicornWorker","--bind","0.0.0.0:8000","--certfile=fullchain.pem","--keyfile=privkey.pem","app:app"]
