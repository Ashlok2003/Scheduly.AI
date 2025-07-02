import streamlit as st
import requests
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Scheduly.AI – A Personal Conversational Calendar Booking Assistant")
st.write("Chat with my assistant to book an appointment on my Google Calendar.")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Type your message (e.g., 'Book a meeting tomorrow at 2 PM for 1 hour with John')"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        logger.debug(f"Sending request to {BACKEND_URL}/chat with message: {user_input}")
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"message": user_input},
            timeout=30,  # Increased timeout to handle potential slow responses
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()  # Raise exception for non-2xx status codes
        agent_response = response.json().get("response", "Error: No response from server")
        logger.debug(f"Received response: {agent_response}")
    except requests.exceptions.Timeout:
        agent_response = "Error: Request timed out. The server took too long to respond. Please try again."
        logger.error(f"Timeout error: {agent_response}")
        st.error(agent_response)
    except requests.exceptions.ConnectionError:
        agent_response = f"Error: Failed to connect to the backend at {BACKEND_URL}. Please check if the server is running."
        logger.error(f"Connection error: {agent_response}")
        st.error(agent_response)
    except requests.exceptions.HTTPError as e:
        agent_response = f"Error: HTTP error occurred. Status code: {e.response.status_code}. {str(e)}"
        logger.error(f"HTTP error: {agent_response}")
        st.error(agent_response)
    except requests.exceptions.RequestException as e:
        agent_response = f"Error: Failed to communicate with the backend. {str(e)}"
        logger.error(f"Request exception: {agent_response}")
        st.error(agent_response)
    except ValueError as e:
        agent_response = "Error: Invalid response format from the server. Please try again."
        logger.error(f"JSON decode error: {str(e)}")
        st.error(agent_response)

    st.session_state.messages.append({"role": "assistant", "content": agent_response})
    with st.chat_message("assistant"):
        st.markdown(agent_response)
