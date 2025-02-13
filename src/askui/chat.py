import streamlit as st
from askui import VisionAgent
import logging
from askui.utils import base64_to_image


def main():
    st.title("Agent Chat")
    
    # Initialize chat history in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Say something"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
            
        # Execute the act command with VisionAgent
        with st.chat_message("assistant"):
            def update_progress(report):
                if isinstance(report, dict):
                    # Display content text
                    if "content" in report:
                        st.write(report["content"])
                    
                    # Display image if available
                    if "image" in report and report["image"]:
                        st.image(base64_to_image(report["image"]))
                else:
                    # Fallback for simple string reports
                    st.write(f"🔄 {report}")

            with VisionAgent(log_level=logging.DEBUG, enable_report=True, report_callback=update_progress) as agent:
                agent.act(prompt, model_name="claude")


if __name__ == "__main__":
    main()
