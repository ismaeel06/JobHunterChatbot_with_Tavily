import requests
import json

class TalentChatbotClient:
    """Client for testing the Talent Scraper Chatbot."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = "test_session_123"
    
    def chat(self, message: str):
        """Send a chat message to the bot."""
        try:
            payload = {
                "message": message,
                "session_id": self.session_id
            }
            
            print(f"👤 You: {message}")
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🤖 Bot: {result['response']}")
                
                if result['search_performed']:
                    print(f"🔍 Search Summary: {result['search_summary']}")
                    print(f"👥 Candidates Found: {result['talent_count']}")
                
                return result
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return None
    
    def reset_conversation(self):
        """Reset the conversation."""
        try:
            response = requests.post(f"{self.base_url}/api/v1/reset-conversation?session_id={self.session_id}")
            if response.status_code == 200:
                print("🔄 Conversation reset successfully")
                return True
            return False
        except Exception as e:
            print(f"❌ Reset error: {e}")
            return False

def main():
    """Interactive chat session."""
    print("🚀 Talent Scraper Chatbot - Interactive Test")
    print("=" * 50)
    print("💡 Try these example requests:")
    print("   - 'Find me 3 senior React developers'")
    print("   - 'I need Python engineers with AI experience'")
    print("   - 'Search for MERN stack freelancers'")
    print("   - 'Hello, what can you help me with?'")
    print("=" * 50)
    
    client = TalentChatbotClient()
    
    # Test health first
    try:
        health = requests.get(f"{client.base_url}/health")
        if health.status_code != 200:
            print("❌ API is not healthy. Make sure the server is running.")
            return
        print("✅ API is healthy and ready!")
    except:
        print("❌ Cannot connect to API. Make sure the server is running on localhost:8000")
        return
    
    print("\n💬 Start chatting! (Type 'quit' to exit, 'reset' to reset conversation)")
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                client.reset_conversation()
                continue
            
            if user_input:
                result = client.chat(user_input)
                if not result:
                    print("❌ Failed to get response. Please try again.")
            else:
                print("⚠️ Please enter a message.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()