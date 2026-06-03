import sqlite3
from tabulate import tabulate

conn = sqlite3.connect("chatbot.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM messages")

rows = cursor.fetchall()

print(
    tabulate(
        rows,
        headers=["ID", "Role", "Content", "Timestamp"],
        tablefmt="grid"
    )
)

conn.close()