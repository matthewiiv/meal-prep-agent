"""
Tool-calling meal prep agent using LangGraph.
Much more flexible than the rigid workflow approach.
"""

import os
from typing import List, Dict, Any, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from .tools import (
    analyze_user_preferences,
    generate_recipe,
    calculate_nutrition_totals,
    optimize_for_waste_reduction,
    evaluate_recipe_feedback
)
from .tesco_real import search_tesco_products_real


class MealPrepState(dict):
    """State for the meal prep agent with message handling."""
    messages: Annotated[List[BaseMessage], add_messages]


class MealPrepAgent:
    """Flexible meal prep agent that uses tools to iteratively create meal plans."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.7)
        
        # Available tools for the agent
        self.tools = [
            analyze_user_preferences,
            search_tesco_products_real,
            generate_recipe,
            calculate_nutrition_totals,
            optimize_for_waste_reduction,
            evaluate_recipe_feedback
        ]
        
        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Create workflow
        self.checkpointer = MemorySaver()
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
    
    def _create_workflow(self) -> StateGraph:
        """Create a flexible tool-calling workflow."""
        workflow = StateGraph(MealPrepState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self.tools))
        
        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        
        return workflow
    
    def _agent_node(self, state: MealPrepState) -> MealPrepState:
        """Agent node that decides what to do next."""
        print("🤖 AGENT: Thinking...")
        
        # System prompt that defines the agent's behavior
        system_prompt = """You are an expert meal prep assistant. Your goal is to help users create 
        personalized weekly meal plans that meet their dietary preferences, macro targets, and constraints.

        You have access to tools that can:
        - Analyze user preferences from their input
        - Search for products in Tesco's catalog  
        - Generate creative recipes using available ingredients
        - Calculate nutritional totals across recipes
        - Optimize recipes to reduce food waste
        - Process feedback to improve existing recipes

        Work iteratively:
        1. Start by understanding the user's needs
        2. Search for suitable ingredients 
        3. Generate initial recipes
        4. Calculate nutrition and check against targets
        5. Optimize for waste reduction
        6. Present the meal plan
        7. Process any feedback and iterate

        Be conversational and explain your reasoning. Ask for clarification when needed.
        """
        
        # Add system message if it's the first interaction
        messages = state["messages"]
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages = [SystemMessage(content=system_prompt)] + messages
        
        # Get response from LLM
        response = self.llm_with_tools.invoke(messages)
        
        return {"messages": [response]}
    
    def _should_continue(self, state: MealPrepState) -> str:
        """Decide whether to continue with tools or end."""
        last_message = state["messages"][-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            print(f"🔧 TOOLS: Calling {len(last_message.tool_calls)} tool(s)")
            return "continue"
        else:
            print("✅ DONE: Agent finished")
            return "end"
    
    def run(self, user_input: str, thread_id: str = "default") -> Dict[str, Any]:
        """Run the agent with user input."""
        config = {"configurable": {"thread_id": thread_id}}
        
        # Add user message to the conversation
        initial_state = {
            "messages": [HumanMessage(content=user_input)]
        }
        
        result = self.app.invoke(initial_state, config)
        return result
    
    def stream_run(self, user_input: str, thread_id: str = "default"):
        """Stream the agent's execution for real-time feedback."""
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)]
        }
        
        for chunk in self.app.stream(initial_state, config):
            yield chunk


if __name__ == "__main__":
    # Test the new agent
    agent = MealPrepAgent()
    
    print("🍽️ New Tool-Calling Meal Prep Agent")
    print("=" * 50)
    
    result = agent.run("I want high-protein meal prep for this week. I have 30 minutes max per meal to cook.")
    
    # Print the conversation
    for message in result["messages"]:
        if isinstance(message, HumanMessage):
            print(f"👤 USER: {message.content}")
        elif isinstance(message, AIMessage):
            print(f"🤖 AGENT: {message.content}")
            if hasattr(message, 'tool_calls') and message.tool_calls:
                print(f"   🔧 Used {len(message.tool_calls)} tool(s)")
        elif isinstance(message, SystemMessage):
            print("🎯 SYSTEM: [System prompt set]")
        print()