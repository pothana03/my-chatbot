from flask import Flask, render_template, request, Response
import ollama
import sqlite3
from datetime import datetime

app = Flask(__name__)

# DATABASE FILE
DATABASE = "chatbot.db"

# SYSTEM PROMPT
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are Buddy, a helpful AI assistant.

Rules:
1. Answer only the user's question.
2. Keep answers short and relevant.
3. Never introduce unrelated topics.
4. If greeted with 'Hi', 'Hello', or similar greetings, respond with a friendly greeting.
5. If the question is unclear, ask for clarification.
6. If you don't know something, say so.
7. Maintain conversation context when relevant.
"""
}


# CREATE DATABASE TABLE
def init_db():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    user_message = request.json.get("message")

    # CONNECT DATABASE
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # CURRENT TIME
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # SAVE USER MESSAGE
    cursor.execute(
        """
        INSERT INTO messages (role, content, timestamp)
        VALUES (?, ?, ?)
        """,
        ("user", user_message, current_time)
    )

    conn.commit()

    # FETCH LAST 4 MESSAGES
    cursor.execute("""
        SELECT role, content
        FROM messages
        ORDER BY id DESC
        LIMIT 4
    """)

    rows = cursor.fetchall()

    # REVERSE TO MAINTAIN CHAT ORDER
    rows.reverse()

    # CONVERT TO OLLAMA FORMAT
    recent_messages = []

    for row in rows:
        recent_messages.append({
            "role": row[0],
            "content": row[1]
        })

    # DEBUG OUTPUT
    print("\n========== MESSAGES SENT TO MODEL ==========\n")

    for msg in recent_messages:
        print(msg)

    print("\n===========================================\n")

    # STREAMING RESPONSE FUNCTION
    def generate():

        bot_reply = ""

        response = ollama.chat(
            model="phi3:mini",
            messages=[SYSTEM_PROMPT] + recent_messages,
            stream=True,
            options={
                "num_predict": 60
            }
        )

        for chunk in response:

            content = chunk.get("message", {}).get("content", "")

            if content:

                bot_reply += content

                yield content

        # ASSISTANT TIMESTAMP
        assistant_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # SAVE BOT RESPONSE
        cursor.execute(
            """
            INSERT INTO messages (role, content, timestamp)
            VALUES (?, ?, ?)
            """,
            ("assistant", bot_reply, assistant_time)
        )

        conn.commit()
        conn.close()

    return Response(
        generate(),
        content_type="text/plain"
    )


# CLEAR DATABASE MEMORY
@app.route("/clear")
def clear_memory():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM messages")

    conn.commit()
    conn.close()

    return {
        "status": "Memory Cleared Successfully"
    }


# INITIALIZE DATABASE
init_db()

if __name__ == "__main__":
    app.run(debug=False)