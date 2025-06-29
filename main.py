"""
Entry point for the meal prep agent.
"""

import os
from dotenv import load_dotenv
from meal_prep_agent.agent import MealPrepAgent

load_dotenv()


def main():
    """Run the meal prep agent."""
    agent = MealPrepAgent()
    
    print("🍽️ Meal Prep Agent Started!")
    print("Ask me to create meal prep recipes based on your preferences.")
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye! Happy meal prepping! 🍽️")
            break
        
        if not user_input:
            continue
        
        try:
            result = agent.run(user_input)
            
            # Print the agent's response
            if result.get("messages"):
                last_message = result["messages"][-1]
                print(f"Agent: {last_message.content}")
        
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()