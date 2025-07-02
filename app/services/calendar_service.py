import asyncio
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from app.core.config import settings
import json
import logging

SCOPES = ['https://www.googleapis.com/auth/calendar']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_calendar_service():
    try:
        logger.debug(f"GOOGLE_CREDENTIALS_JSON: {repr(settings.GOOGLE_CREDENTIALS_JSON)}")
        raw_json = settings.GOOGLE_CREDENTIALS_JSON
        if not raw_json:
            raise Exception("GOOGLE_CREDENTIALS_JSON is missing or empty")

        credentials_info = settings.GOOGLE_CREDENTIALS_JSON
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=SCOPES
        )
        return build('calendar', 'v3', credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to initialize calendar service: {str(e)}")
        raise Exception(f"Failed to initialize calendar service: {str(e)}")

async def check_availability(calendar_id: str, start_str: str, duration: str) -> bool:
    try:
        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end = start + timedelta(minutes=int(duration))

        service = get_calendar_service()
        events_result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: service.events().list(
                calendarId=calendar_id,
                timeMin=start.isoformat() + 'Z',
                timeMax=end.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
        )

        events = events_result.get('items', [])
        logger.info(f"Checked availability for {calendar_id} at {start_str} for {duration} minutes: {'Available' if len(events) == 0 else 'Not available'}")
        return len(events) == 0
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        raise Exception(f"Failed to check availability: {str(e)}")

async def create_event(calendar_id: str, start_str: str, duration: str, summary: str) -> str:
    try:
        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end = start + timedelta(minutes=int(duration))

        event = {
            'summary': summary,
            'start': {
                'dateTime': start.isoformat() + 'Z',
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end.isoformat() + 'Z',
                'timeZone': 'UTC'
            }
        }

        service = get_calendar_service()
        event_result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: service.events().insert(calendarId=calendar_id, body=event).execute()
        )

        logger.info(f"Created event: {summary} at {start_str} for {duration} minutes")
        return f"Appointment booked: {summary} at {start_str} for {duration} minutes. Event link: {event_result.get('htmlLink')}"
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise Exception(f"Failed to create event: {str(e)}")
