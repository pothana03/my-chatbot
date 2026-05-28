from flask import Flask, render_template, request, Response
import ollama
import json
import os
from datetime import datetime

app = Flask(__name__)

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are Buddy, a helpful assistant. Reply briefly and clearly."
}

# ---------------- MEMORY FILE ----------------
MEMORY_FILE = "memory.json"

# ---------------- LOAD MEMORY ----------------
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        conversation_history = json.load(f)
else:
    conversation_history = [SYSTEM_PROMPT]

# ---------------- LONG TERM MEMORY ----------------
memory_summary = ""


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- MEMORY SUMMARY (optional future use) ----------------
def update_memory_summary():
    global memory_summary

    last_msgs = conversation_history[-10:]

    prompt = {
        "role": "user",
        "content": f"Summarize user info in 1-2 lines:\n{last_msgs}"
    }

    response = ollama.chat(
        model="phi3:mini",
        messages=[prompt]
    )

    memory_summary = response["message"]["content"]


# ---------------- CHAT ROUTE (STREAMING) ----------------
@app.route("/chat", methods=["POST"])
def chat():

    global conversation_history, memory_summary

    user_message = request.json.get("message")

    # store user message
    conversation_history.append({
        "role": "user",
        "content": user_message,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    # limit memory
    if len(conversation_history) > 100:
        conversation_history = conversation_history[-100:]

    # short context
    recent_messages = conversation_history[-6:]

    def generate():

        bot_reply = ""

        # build message stack safely
        messages = [SYSTEM_PROMPT]

        if memory_summary.strip():
            messages.append({
                "role": "system",
                "content": f"Memory: {memory_summary}"
            })

        messages += recent_messages

        response = ollama.chat(
            model="phi3:mini",
            messages=messages,
            stream=True,
            options={"num_predict": 120}
        )

        for chunk in response:

            content = chunk.get("message", {}).get("content", "")

            if content:
                bot_reply += content
                yield content

        # store assistant response
        conversation_history.append({
            "role": "assistant",
            "content": bot_reply,
            "time": datetime.now().strftime("%H:%M:%S")
        })

        # save memory
        with open(MEMORY_FILE, "w") as f:
            json.dump(conversation_history, f, indent=4)

        # update memory occasionally
        if len(conversation_history) % 10 == 0:
            update_memory_summary()

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ---------------- CLEAR MEMORY ----------------
@app.route("/clear", methods=["GET"])
def clear_memory():

    global conversation_history, memory_summary

    conversation_history = [SYSTEM_PROMPT]
    memory_summary = ""

    with open(MEMORY_FILE, "w") as f:
        json.dump(conversation_history, f, indent=4)

    return {"status": "Memory Cleared Successfully"}


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=False, threaded=True)