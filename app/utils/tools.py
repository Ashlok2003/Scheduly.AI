import json
from langchain.tools import Tool
from app.services.calendar_service import check_availability, create_event
from dateutil import parser
import asyncio
import logging
import re

logger = logging.getLogger(__name__)


def safe_json_loads(input_str: str):
    try:
        logger.debug(f"Raw input for JSON: {repr(input_str)}")
        match = re.search(r'\{.*?\}', input_str.strip(), re.DOTALL)
        if not match:
            raise ValueError("No valid JSON object found.")
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {repr(input_str)}\nError: {e}")
        raise


async def check_availability_tool(input_str: str) -> str:
    try:
        logger.debug(f"Raw check_availability_tool input: {repr(input_str)}")
        input_data = safe_json_loads(input_str)

        calendar_id = input_data.get("calendar_id", "primary")
        date_time = input_data.get("date_time")
        duration = input_data.get("duration")

        if not all([calendar_id, date_time, duration]):
            logger.error(f"Missing fields: calendar_id={calendar_id}, date_time={date_time}, duration={duration}")
            return "Error: Missing required fields for availability check (calendar_id, date_time, duration)"

        dt = parser.parse(date_time).isoformat()
        is_free = await check_availability(calendar_id, dt, duration)
        return json.dumps({"available": is_free})

    except Exception as e:
        logger.error(f"Error in check_availability_tool: {str(e)}", exc_info=True)
        return f"Error checking availability: {str(e)}"

async def book_appointment_tool(input_str: str) -> str:
    try:
        logger.debug(f"Raw book_appointment_tool input: {repr(input_str)}")
        input_data = safe_json_loads(input_str)

        calendar_id = input_data.get("calendar_id", "primary")
        date_time = input_data.get("date_time")
        duration = input_data.get("duration")
        description = input_data.get("description")

        if not all([calendar_id, date_time, duration, description]):
            logger.error(f"Missing fields: calendar_id={calendar_id}, date_time={date_time}, duration={duration}, description={description}")
            return "Error: Missing required fields for booking (calendar_id, date_time, duration, description)"

        dt = parser.parse(date_time).isoformat()
        is_free = await check_availability(calendar_id, dt, duration)
        if not is_free:
            return json.dumps({"success": False, "message": "Time slot not available"})

        result = await create_event(calendar_id, dt, duration, description)
        return json.dumps({"success": True, "message": result})

    except Exception as e:
        logger.error(f"Error in book_appointment_tool: {str(e)}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})

tools = [
    Tool(
        name="check_availability",
        func=check_availability_tool,
        description=(
            "Check if a time slot is available on the user's calendar. "
            "Input must be a JSON string with fields: calendar_id (default 'primary'), "
            "date_time (ISO format), duration (minutes as string). "
            "Example: '{\"calendar_id\": \"primary\", \"date_time\": \"2025-07-04T14:00:00\", \"duration\": \"60\"}'"
        ),
        coroutine=check_availability_tool
    ),
    Tool(
        name="book_appointment",
        func=book_appointment_tool,
        description=(
            "Book an appointment on the user's calendar. "
            "Input must be a JSON string with fields: calendar_id (default 'primary'), "
            "date_time (ISO format), duration (minutes as string), description. "
            "Example: '{\"calendar_id\": \"primary\", \"date_time\": \"2025-07-04T14:00:00\", \"duration\": \"60\", \"description\": \"Meeting with Ashlok\"}'"
        ),
        coroutine=book_appointment_tool
    )
]
