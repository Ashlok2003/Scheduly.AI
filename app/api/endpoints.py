import logging
from fastapi import APIRouter, Request
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from app.utils.tools import tools
from app.core.config import settings
from datetime import datetime
import pytz
import asyncio

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=settings.GEMINI_API_KEY
)

react_prompt = PromptTemplate.from_template(
    """You are an AI assistant that helps users book appointments on Google Calendar.

Available tools:
{tools}

Tool names:
{tool_names}

User input: {input}

Instructions:
- Always follow this format:
  Thought: <what you're thinking>
  Action: <tool_name>
  Action Input: <JSON string with inputs>
  Observation: <tool output>
  Thought: <response after observation>
  Final Answer: <natural language reply>

- Booking Requests:
  - Extract calendar_id (default: 'primary')
  - Extract date_time (e.g., 'tomorrow at 2 PM') and convert to ISO 8601 (e.g., '2025-07-04T14:00:00')
  - Extract duration in minutes as a string (e.g., '60')
  - Extract description (e.g., 'Meeting with Ashlok')
  - Always call check_availability before calling book_appointment.
  - Only book if the time slot is available.

- Date Notes:
  - Interpret 'tomorrow' relative to IST timezone and current time.
  - All date_time values must be in ISO format with no trailing 'Z'.

- If any required field is missing, reply:
  Final Answer: Error: Missing required fields (e.g., date, time, duration, description)

- For confirmations, reply:
  Final Answer: Thank you for the confirmation. The meeting is scheduled.

{agent_scratchpad}"""
)

memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=react_prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3
)

@router.post("/chat")
async def chat(request: Request):
    try:
        logger.debug("Received request to /chat")
        data = await request.json()
        user_message = data.get("message", "")
        logger.debug(f"User message: {user_message}")

        if not user_message:
            logger.warning("No message provided in request")
            return {"error": "No message provided", "status": 400}

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')
        logger.debug(f"Current time: {current_time}")

        formatted_input = f"""
            Today's date and time: {current_time}

            User input: {user_message}
        """
        logger.debug(f"Formatted input: {formatted_input}")

        logger.debug("Starting AgentExecutor")
        response = await asyncio.wait_for(
            agent_executor.ainvoke({"input": formatted_input}),
            timeout=25
        )
        logger.debug(f"AgentExecutor response: {response}")

        agent_output = response.get("output", "Error: No output from agent")
        logger.debug(f"Final agent output: {agent_output}")

        return {"response": agent_output, "status": 200}
    except asyncio.TimeoutError:
        logger.error("AgentExecutor timed out")
        return {"error": "Server error: Agent processing timed out", "status": 500}
    except ValueError as e:
        logger.error(f"Invalid JSON in request: {str(e)}", exc_info=True)
        return {"error": f"Invalid request format: {str(e)}", "status": 400}
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        return {"error": f"Server error: {str(e)}", "status": 500}
