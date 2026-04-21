# agent.py
# Production-style Level 3 Agent for LifeAtlas LPI MCP Server
# Python + Ollama + Real MCP subprocess calls

import subprocess
import json
import requests
import sys
import time

OLLAMA_MODEL = "qwen2.5:1.5b"


# ----------------------------
# Start MCP Server
# ----------------------------
def start_server():
    process = subprocess.Popen(
        ["node", "dist/src/index.js"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    time.sleep(2)
    return process


# ----------------------------
# Send MCP Request
# ----------------------------
def send_request(process, payload):
    process.stdin.write(json.dumps(payload) + "\n")
    process.stdin.flush()

    line = process.stdout.readline()
    return json.loads(line)


# ----------------------------
# Call Tool
# ----------------------------
def call_tool(process, tool_name, arguments={}):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    response = send_request(process, payload)
    return response


# ----------------------------
# Ollama Call
# ----------------------------
def ask_ollama(prompt):
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    res = requests.post(url, json=payload)
    return res.json()["response"]


# ----------------------------
# Main Agent Logic
# ----------------------------
def run_agent(question):
    process = start_server()

    try:
        source1 = call_tool(process, "smile_overview")
        source2 = call_tool(process, "query_knowledge", {
            "query": question
        })
        source3 = call_tool(process, "get_case_studies")

        final_prompt = f"""
You are an expert LifeAtlas AI assistant.

USER QUESTION:
{question}

SOURCE 1: smile_overview
{json.dumps(source1, indent=2)}

SOURCE 2: query_knowledge
{json.dumps(source2, indent=2)}

SOURCE 3: get_case_studies
{json.dumps(source3, indent=2)}

TASK:
1. Answer clearly
2. Summarize insights
3. Mention which tool provided what
4. Be concise and professional
"""

        answer = ask_ollama(final_prompt)

        print("\n==============================")
        print("FINAL ANSWER")
        print("==============================\n")
        print(answer)

    finally:
        process.kill()


# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    q = input("Ask a question: ")
    run_agent(q)