"""
LangGraph-based meal prep agent.
"""

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class MealPrepState(TypedDict):
    messages: List[BaseMessage]
    preferences: Optional[dict]
    current_recipes: Optional[List[dict]]
    feedback: Optional[str]
    iteration_count: int


class MealPrepAgent:
    def __init__(self):
        self.checkpointer = MemorySaver()
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
    
    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(MealPrepState)
        
        workflow.add_node("analyze_preferences", self._analyze_preferences)
        workflow.add_node("generate_recipes", self._generate_recipes)
        workflow.add_node("process_feedback", self._process_feedback)
        workflow.add_node("finalize_meal_plan", self._finalize_meal_plan)
        
        workflow.add_edge(START, "analyze_preferences")
        workflow.add_edge("analyze_preferences", "generate_recipes")
        workflow.add_edge("generate_recipes", "finalize_meal_plan")
        workflow.add_edge("process_feedback", "generate_recipes")
        workflow.add_edge("finalize_meal_plan", END)
        
        return workflow
    
    def _analyze_preferences(self, state: MealPrepState) -> MealPrepState:
        """Analyze user preferences for meal planning."""
        print("🔍 CALLING: _analyze_preferences")
        # Placeholder for preference analysis logic
        state["preferences"] = {
            "dietary_restrictions": [],
            "macro_targets": {},
            "cooking_time_limit": 30,
            "complexity_level": "medium"
        }
        
        state["messages"].append(
            AIMessage(content="Analyzed preferences for meal planning")
        )
        return state
    
    def _generate_recipes(self, state: MealPrepState) -> MealPrepState:
        """Generate meal prep recipes based on preferences."""
        print("🍳 CALLING: _generate_recipes")
        # Placeholder for recipe generation logic
        state["current_recipes"] = [
            {"name": "Sample Recipe", "ingredients": [], "instructions": []}
        ]
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
        state["messages"].append(
            AIMessage(content=f"Generated recipes (iteration {state['iteration_count']})")
        )
        return state
    
    def _process_feedback(self, state: MealPrepState) -> MealPrepState:
        """Process user feedback and adjust recipes."""
        print("💬 CALLING: _process_feedback")
        # Placeholder for feedback processing logic
        state["messages"].append(
            AIMessage(content="Processed feedback and adjusting recipes")
        )
        return state
    
    def _finalize_meal_plan(self, state: MealPrepState) -> MealPrepState:
        """Finalize the meal plan for the week."""
        print("✅ CALLING: _finalize_meal_plan")
        # Placeholder for finalization logic
        state["messages"].append(
            AIMessage(content="Finalized meal plan for the week")
        )
        return state
    
    def run(self, user_input: str, thread_id: str = "default") -> dict:
        """Run the meal prep agent with user input."""
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "preferences": None,
            "current_recipes": None,
            "feedback": None,
            "iteration_count": 0
        }
        
        result = self.app.invoke(initial_state, config)
        return result


if __name__ == "__main__":
    agent = MealPrepAgent()
    
    # Visualize the workflow
    try:
        print("Workflow visualization:")
        print(agent.app.get_graph().draw_ascii())
    except Exception as e:
        print(f"Could not draw graph: {e}")
    
    result = agent.run("I want meal prep recipes for this week")
    print("Final state:", result)