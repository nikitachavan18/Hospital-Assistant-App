from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "Hospital_Assistant" / ".env")
 
from Hospital_Assistant.agent import OrthoAgent  # noqa: E402
 
 
def main():
    agent = OrthoAgent()
    print("Orthodontic Assistant (type 'quit' to exit)\n")
    while True:
        user = input("You: ").strip()
        if user.lower() in {"quit", "exit"}:
            break
        if user:
            print(f"\nAssistant: {agent.chat(user)}\n")
 
 
if __name__ == "__main__":
    main()
 