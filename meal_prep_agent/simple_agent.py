#!/usr/bin/env python3
"""
Simple meal prep agent using LangGraph with Tesco integration.
"""

from typing import Annotated, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from .tesco_real import search_tesco_products_real

# System prompt adapted from your GPT
MEAL_PREP_SYSTEM_PROMPT = """You are a meal prep planning expert that creates customized weekly meal-prep plans using real Tesco products and pricing.

USER PROFILE:
- Wants meals to always include meat (except chicken thighs)
- Prefers quick and easy cooking
- Has no allergies
- Needs 18 meals per week
- Follows a 2500 calorie/day target, with meals between 600–650 kcal each
- Wants a strict macronutrient breakdown of 45% carbs, 30% protein, 25% fat
- Prefers cheese over oil as a fat source (cheese preferred where possible, but not mandatory in every recipe)
- Shops at Tesco and expects price and nutritional accuracy based on Tesco listings
- Likes the style of The Salad Project and Farmer J
- Prefers low-budget, minimal food waste (optimize for Tesco pack sizes)
- Will not spend more than £3 per meal
- Has no kitchen equipment limitations
- Prefers total cooking and prep time to be no more than 1.5 hours
- Favourite carbs are rice and potatoes

MEAL PLANNING PROCESS:
1. Generate **four candidate recipes** that match the above style. Include:
   • Ingredients (with Tesco-compatible sizes)
   • Calories and **strictly calculated and double-checked** macros per portion (45% carbs, 30% protein, 25% fat)
   • Tesco price per portion (accurate using real Tesco data)
   • Cooking time
   • Emphasis on **bold, flavourful seasoning and marinades**
   • Prefer cheese as fat source over oil where practical

2. Automatically pick the **best two recipes** from the four provided based on flavour, variety, and budget, unless the user prefers to choose.

3. Prepare **nine servings of each of the selected two recipes**.

4. Once recipes are confirmed, output:
   A. **Finalized Meal Plan Table** (Day-by-day, Meal-by-meal)
   B. **Consolidated Shopping Basket** with real Tesco data
   C. **Batch-Cooking Instructions** (if needed)

IMPORTANT: Always use the search_tesco_products_real tool to get current pricing and product information from Tesco. Use the nutrition data (per 100g) from Tesco to calculate accurate macros.

Tone is helpful, concise, and upbeat. Avoid fluff. Emphasize speed, value, strong flavours, and minimal waste. Always double-check and validate macro calculations before presenting them."""

class MealPrepState(dict):
    """State for the meal prep agent."""
    messages: Annotated[List[BaseMessage], add_messages]

def create_meal_prep_agent():
    """Create the simple meal prep agent."""
    
    # Initialize the LLM with tools - using reasoning model
    llm = ChatOpenAI(model="o3", temperature=1.0)
    tools = [search_tesco_products_real]
    llm_with_tools = llm.bind_tools(tools)
    
    # Create tool node
    tool_node = ToolNode(tools)
    
    def agent_node(state: MealPrepState):
        """Main agent reasoning node."""
        messages = state["messages"]
        
        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=MEAL_PREP_SYSTEM_PROMPT)] + messages
        
        print("🧠 o3 is thinking deeply about your meal prep request...")
        print("⏳ This may take 30-90 seconds for complex reasoning...")
        
        import time
        start_time = time.time()
        
        # Show periodic thinking indicators
        import threading
        thinking = True
        
        def show_thinking():
            dots = 0
            while thinking:
                print(f"\r💭 Reasoning{'.' * (dots % 4)}{' ' * (3 - (dots % 4))}", end="", flush=True)
                time.sleep(1)
                dots += 1
        
        thinking_thread = threading.Thread(target=show_thinking)
        thinking_thread.daemon = True
        thinking_thread.start()
        
        try:
            # Get response from LLM
            response = llm_with_tools.invoke(messages)
            thinking = False
            elapsed = time.time() - start_time
            print(f"\r✨ o3 finished reasoning in {elapsed:.1f} seconds!           ")
            return {"messages": [response]}
        finally:
            thinking = False
    
    # Create the graph
    workflow = StateGraph(MealPrepState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
    )
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    app = workflow.compile()
    return app

def run_meal_prep_agent(user_input: str) -> str:
    """Run the meal prep agent with user input."""
    
    agent = create_meal_prep_agent()
    
    # Initial state
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    
    # Run the agent
    result = agent.invoke(initial_state)
    
    # Return the last assistant message
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        return last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    return "I'm ready to help with your meal prep planning!"

if __name__ == "__main__":
    # Test the agent
    response = run_meal_prep_agent("Hi! I'd like a meal prep plan for this week.")
    print(response)