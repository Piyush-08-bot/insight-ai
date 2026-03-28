import os
import sys
from pathlib import Path

# Add project root to sys.path
root_path = "/Users/piyushraj/Desktop/ProjX/ai-service"
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from insight.chains.qa_chain import get_llm

def test_provider_routing():
    providers = ["openai", "anthropic", "google", "groq", "ollama"]
    
    print("🧪 Testing Provider Routing Logic...")
    print("-" * 40)
    
    # Mock environment keys for testing
    os.environ["OPENAI_API_KEY"] = "mock_key"
    os.environ["ANTHROPIC_API_KEY"] = "mock_key"
    os.environ["GOOGLE_API_KEY"] = "mock_key"
    os.environ["GROQ_API_KEY"] = "mock_key"

    for p in providers:
        print(f"Testing provider: [ {p} ]")
        try:
            llm = get_llm(provider=p)
            print(f"✅ Success: Initialized {type(llm).__name__}")
        except ImportError as e:
            print(f"⚠️  Dependency Missing: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 40)

if __name__ == "__main__":
    test_provider_routing()
