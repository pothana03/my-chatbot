from flask import Flask, render_template, request, jsonify
import ollama

app = Flask(__name__)

# System prompt
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are Buddy, a friendly personal AI assistant.
You are helpful, smart, concise, and friendly.
Always reply clearly and naturally.
"""
}

# Store conversation
conversation_history = [SYSTEM_PROMPT]


# Home route
@app.route("/")
def home():
    return render_template("index.html")


# Chat route
@app.route("/chat", methods=["POST"])
def chat():

    try:

        # Get user message
        data = request.get_json()

        user_message = data.get("message")

        if not user_message:
            return jsonify({
                "response": "Please type something."
            })

        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Send to Ollama
        response = ollama.chat(
            model="llama3.2",
            messages=conversation_history
        )

        # Extract AI reply
        bot_reply = response["message"]["content"]

        # Save assistant reply
        conversation_history.append({
            "role": "assistant",
            "content": bot_reply
        })

        # Return response
        return jsonify({
            "response": bot_reply
        })

    except Exception as e:

        print("ERROR:", e)

        return jsonify({
            "response": "Buddy is having trouble connecting to Ollama."
        })


# Run app
if __name__ == "__main__":
    app.run(debug=True)