from fastapi import FastAPI
from app.api.endpoints import router

app = FastAPI(title="Scheduly.AI U+002d Conversational Calendar Booking Assistant")

app.include_router(router)
