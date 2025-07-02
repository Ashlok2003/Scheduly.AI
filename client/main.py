import streamlit as st
import requests

st.title("Appointment Booking Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    response = requests.post("http://localhost:8000/chat", json={"message": user_input})
    agent_response = response.json()["response"]

    st.session_state.messages.append({"role": "assistant", "content": agent_response})
    with st.chat_message("assistant"):
        st.markdown(agent_response)
