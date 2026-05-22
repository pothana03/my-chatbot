import ollama
SYSTEM_PROMPT = {
    "role": "system",
    "content": """You are the user's personal AI assistant named 'Buddy'. You are helpful, friendly and concise in your responses. You always greet the user warmly and answer questions clearly. If you don't know something, you honestly say so."""}

def get_response(user_input: str, history: list) -> str:
    history.append({
        "role": "user",
        "content": user_input
    })
    
    response = ollama.chat(
        model="llama3.2",
        messages=history
    )
    
    assistant_message = response["message"]["content"]
    history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    return assistant_message

def main():
    print("🤖 ChatBot is running! Type 'quit' to exit.\n")
    history = [SYSTEM_PROMPT]
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Bot: Goodbye! Have a great day!")
            break
        response = get_response(user_input, history)
        print(f"Bot: {response}\n")

if __name__ == "__main__":
    main()