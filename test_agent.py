"""
Test the simple meal prep agent with o3 reasoning model.
"""

import os
from dotenv import load_dotenv
from meal_prep_agent.simple_agent import run_meal_prep_agent

# Load environment variables
load_dotenv()

def test_agent():
    """Test the simple meal prep agent with o3 reasoning model."""
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables!")
        print("Please set your OpenAI API key in a .env file")
        print("Add: OPENAI_API_KEY=your_openai_key_here")
        return
    
    print("🧠 Testing Simple Meal Prep Agent with o3 Reasoning Model")
    print("=" * 60)
    
    # Test queries - focused on meal planning
    test_queries = [
        "Hi! I'd like a meal prep plan for this week. Can you create 4 candidate recipes and pick the best 2?",
        "I want bold flavors with beef and rice, staying under £3 per meal",
        "Create a cheese-heavy recipe with chicken (not thighs) that fits my macro targets"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔵 Test {i}: {query}")
        print("-" * 50)
        
        try:
            print("🤖 Agent Response:")
            response = run_meal_prep_agent(query)
            print(response)
            
            print(f"\n✅ Test {i} completed successfully!")
            
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)
    
    print("\n🏁 All tests completed!")


def interactive_test():
    """Interactive test mode - chat with the agent."""
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found!")
        return
    
    print("🍽️ Interactive Meal Prep Agent (o3 Reasoning)")
    print("Type 'quit' to exit")
    print("=" * 50)
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye! Happy meal prepping!")
            break
        
        if not user_input:
            continue
        
        try:
            print("\n🤖 Agent:")
            response = run_meal_prep_agent(user_input)
            print(response)
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Choose test mode
    mode = input("Choose mode:\n1. Automated tests\n2. Interactive chat\nEnter 1 or 2: ").strip()
    
    if mode == "2":
        interactive_test()
    else:
        test_agent()