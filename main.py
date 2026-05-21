import ollama

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
    history = []
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