import os
import uuid
import streamlit as st
import boto3
from botocore.exceptions import BotoCoreError, ClientError
 
# Configuration
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
 
# environment variables 
AGENT_ID = os.getenv("BEDROCK_AGENT_ID", "").strip()
AGENT_ALIAS_ID = os.getenv("BEDROCK_AGENT_ALIAS_ID", "").strip()
 
session = boto3.Session(region_name=REGION)
client = session.client("bedrock-agent-runtime")
 
# Streamlit UI 
st.set_page_config(page_title="Uni Degree Navigator", page_icon="🎓")
st.title("🎓 Uni Degree Navigator")
 
if not AGENT_ID or not AGENT_ALIAS_ID:
    st.warning(
        "Missing BEDROCK_AGENT_ID or BEDROCK_AGENT_ALIAS_ID. "
        "Set them in your terminal before running."
    )
    st.code(
    '$env:BEDROCK_AGENT_ID="YOUR_AGENT_ID"\n'
    '$env:BEDROCK_AGENT_ALIAS_ID="YOUR_AGENT_ALIAS_ID"\n'
    '$env:AWS_PROFILE="your-aws-profile"\n'
    '$env:AWS_DEFAULT_REGION="us-east-1"\n'
    'python -m streamlit run app.py',
    language="powershell"
    )
    st.stop()
 
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
 
def invoke_agent(prompt: str) -> str:
    try:
        resp = client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=st.session_state.session_id,
            inputText=prompt
        )
 
        parts = []
 
        for event in resp.get("completion", []):
            # Most common: chunk bytes
            if "chunk" in event and event["chunk"].get("bytes"):
                parts.append(event["chunk"]["bytes"].decode("utf-8", errors="ignore"))
 
            # Some SDKs: payload bytes
            elif "payload" in event and event["payload"].get("bytes"):
                parts.append(event["payload"]["bytes"].decode("utf-8", errors="ignore"))
 
            # Trace / metadata events (ignore)
            else:
                continue
 
        return "".join(parts).strip() or "No response returned."
 
    except ClientError as e:
        msg = e.response.get("Error", {}).get("Message", str(e))
        code = e.response.get("Error", {}).get("Code", "ClientError")
        return f"Error: {code} - {msg}"
 
    except (BotoCoreError, Exception) as e:
        return f"Error: {str(e)}"
 
# Rendering chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
 
user_input = st.chat_input("Ask about degrees, subjects, or study plans...")
 
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
 
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = invoke_agent(user_input)
        st.write(answer)
 
    st.session_state.messages.append({"role": "assistant", "content": answer})
 
if st.button("New chat"):
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.rerun()