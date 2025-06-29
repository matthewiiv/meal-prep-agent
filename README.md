# Meal Prep Agent

A LangGraph-based intelligent agent that creates personalized meal prep recipes using the Tesco API. The agent considers your dietary preferences, macro targets, cooking time constraints, and complexity preferences to generate optimized weekly meal plans.

## Features

- **Intelligent Recipe Generation**: Creates meal prep recipes tailored to your specific needs
- **Macro Optimization**: Ensures recipes meet your nutritional targets
- **Feedback Loops**: Iteratively improves recipes based on your feedback
- **Waste Reduction**: Optimizes ingredient usage to minimize food waste
- **Tesco Integration**: Uses real product data and pricing from Tesco API

## Setup

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Run the agent**:
   ```bash
   poetry run python main.py
   ```

## Usage

Start a conversation with the agent about your meal prep needs:

```
You: I need meal prep for this week. I want high protein, low carb meals that take less than 30 minutes to cook.
Agent: I'll create a meal plan based on your preferences...
```

## Project Structure

```
meal-prep/
├── meal_prep_agent/
│   ├── __init__.py
│   └── agent.py          # Main LangGraph agent
├── main.py               # Entry point
├── .env.example          # Environment variables template
└── pyproject.toml        # Poetry configuration
```

## Development Status

This is the initial skeleton setup. Future implementations will include:
- Tesco API integration
- Advanced recipe generation
- Nutritional analysis
- Cost optimization
- Feedback processing