from flask import Flask, render_template, request, jsonify
import ollama
import json
import os

app = Flask(__name__)

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are Buddy, a helpful AI assistant."
}

MEMORY_FILE = "memory.json"


# LOAD MEMORY
if os.path.exists(MEMORY_FILE):

    with open(MEMORY_FILE, "r") as f:
        conversation_history = json.load(f)

else:
    conversation_history = [SYSTEM_PROMPT]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    global conversation_history

    user_message = request.json.get("message")

    # Add user message
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # ONLY LAST 6 MESSAGES
    recent_messages = conversation_history[-6:]

    # AI RESPONSE
    response = ollama.chat(
        model="phi3:mini",
        messages=[SYSTEM_PROMPT] + recent_messages
    )

    bot_reply = response["message"]["content"]

    # Save bot reply
    conversation_history.append({
        "role": "assistant",
        "content": bot_reply
    })

    # SAVE MEMORY TO JSON
    with open(MEMORY_FILE, "w") as f:
        json.dump(conversation_history, f, indent=4)

    return jsonify({
        "response": bot_reply
    })


if __name__ == "__main__":
    app.run(debug=False)