from flask import Flask, render_template, request, Response
import ollama
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)

# DATABASE FILE
DATABASE = "chatbot.db"

import os

print("Current directory:", os.getcwd())
print("Database path:", os.path.abspath(DATABASE))

# SYSTEM PROMPT
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are Buddy, a helpful AI assistant.

Rules:
- Respond only in English.
- Never output Japanese, Chinese, Korean, or other languages unless explicitly requested.
- Answer only the user's question.
- Keep answers concise and relevant.
- Do not generate exercises, instructions, or unrelated text.
- If greeted, respond with a simple greeting.
"""
}


# CREATE DATABASE TABLE
def init_db():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,
        content TEXT,
        timestamp TEXT
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        title TEXT,
        created_at TEXT
    )
""")

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/new_session", methods=["POST"])
def new_session():

    session_id = str(uuid.uuid4())

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions
        (session_id, title, created_at)
        VALUES (?, ?, ?)
    """, (
        session_id,
        "New Chat",
        created_at
    ))

    conn.commit()

    conn.close()

    return {
        "session_id": session_id
    }

@app.route("/sessions")
def get_sessions():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id,
               title,
               created_at
        FROM sessions
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    sessions = []

    for row in rows:

        sessions.append({
            "session_id": row[0],
            "title": row[1],
            "created_at": row[2]
        })

    return sessions

@app.route("/chat", methods=["POST"])
def chat():

    session_id = request.json.get("session_id")
    user_message = request.json.get("message")

    print("SESSION ID:", session_id)
    print("USER MESSAGE:", user_message)

    # CONNECT DATABASE
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # CURRENT TIME
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # SAVE USER MESSAGE
    cursor.execute(
    """
    INSERT INTO messages
    (session_id, role, content, timestamp)
    VALUES (?, ?, ?, ?)
    """,
    (session_id, "user", user_message, current_time)
)

    conn.commit()

    # FETCH LAST 4 MESSAGES
    cursor.execute("""
    SELECT role, content
    FROM messages
    WHERE session_id = ?
    ORDER BY id DESC
    LIMIT 4
""", (session_id,))

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
                "num_predict": 120,
                "temperature": 0.3
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
    INSERT INTO messages
    (session_id, role, content, timestamp)
    VALUES (?, ?, ?, ?)
    """,
    (session_id, "assistant", bot_reply, assistant_time)
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

print(app.url_map)

if __name__ == "__main__":
    app.run(debug=True)