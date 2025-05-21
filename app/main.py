from fastapi import FastAPI
from app.api import auth, crawler, posts
from app.core.db import Base, engine

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(crawler.router, tags=["Crawler"])
app.include_router(posts.router, tags=["Posts"])
