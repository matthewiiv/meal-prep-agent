"""
Test the full meal prep agent with free Tesco scraper.
"""

import os
from dotenv import load_dotenv
from meal_prep_agent.agent_v2 import MealPrepAgent

# Load environment variables
load_dotenv()

def test_agent():
    """Test the meal prep agent with real user input."""
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables!")
        print("Please set your OpenAI API key in a .env file")
        print("Add: OPENAI_API_KEY=your_openai_key_here")
        return
    
    print("🤖 Testing Meal Prep Agent with Free Tesco Scraper")
    print("=" * 60)
    
    # Create agent
    agent = MealPrepAgent()
    
    # Test queries
    test_queries = [
        "I want high-protein meal prep for this week. I have 30 minutes max per meal to cook.",
        "Find me some chicken breast options from Tesco",
        "Create a simple recipe using chicken and vegetables"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔵 Test {i}: {query}")
        print("-" * 50)
        
        try:
            # Run the agent
            result = agent.run(query, thread_id=f"test_{i}")
            
            # Print the conversation
            print("💬 Conversation:")
            for message in result["messages"]:
                if hasattr(message, 'content'):
                    # Determine message type
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        print(f"🤖 AGENT: {message.content}")
                        print(f"   🔧 Called {len(message.tool_calls)} tool(s)")
                        for tool_call in message.tool_calls:
                            print(f"      - {tool_call['name']}")
                    elif message.content:
                        speaker = "👤 USER" if "HumanMessage" in str(type(message)) else "🤖 AGENT"
                        print(f"{speaker}: {message.content}")
            
            print(f"\n✅ Test {i} completed successfully!")
            
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
        
        print("\n" + "="*60)
    
    print("\n🏁 All tests completed!")


def interactive_test():
    """Interactive test mode - chat with the agent."""
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found!")
        return
    
    print("🍽️ Interactive Meal Prep Agent")
    print("Type 'quit' to exit")
    print("=" * 40)
    
    agent = MealPrepAgent()
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye! Happy meal prepping!")
            break
        
        if not user_input:
            continue
        
        try:
            result = agent.run(user_input)
            
            # Print agent's last response
            if result.get("messages"):
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    print(f"🤖 Agent: {last_message.content}")
                    
                    # Show if tools were used
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        print(f"   🔧 Used tools: {[tc['name'] for tc in last_message.tool_calls]}")
        
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Choose test mode
    mode = input("Choose mode:\n1. Automated tests\n2. Interactive chat\nEnter 1 or 2: ").strip()
    
    if mode == "2":
        interactive_test()
    else:
        test_agent()