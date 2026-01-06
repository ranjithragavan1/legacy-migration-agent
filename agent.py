import os
import ast
import re  # Added regex for cleaner stripping
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from google.api_core.exceptions import ResourceExhausted

# Load environment variables
load_dotenv()

# 1. Define the State
class AgentState(TypedDict):
    cobol_code: str
    explanation: Optional[str]
    python_code: Optional[str]

# 2. Initialize the Model
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    temperature=0
)

# --- THE UNIVERSAL UNWRAPPER & SCRUBBER ---
def call_gemini_safe(prompt_text):
    """
    Calls Gemini and handles:
    1. Parsing complex list/string responses.
    2. SCRUBBING markdown code blocks (```python) so output is raw code.
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt_text)])
        content = response.content
        final_text = ""

        # Step 1: Unwrap the content (List vs String)
        if isinstance(content, list):
            final_text = "".join([b.get('text', '') for b in content if b.get('type') == 'text'])
        
        elif isinstance(content, str) and content.strip().startswith("[{") and "type" in content:
            try:
                parsed_content = ast.literal_eval(content)
                if isinstance(parsed_content, list):
                    final_text = "".join([b.get('text', '') for b in parsed_content if b.get('type') == 'text'])
            except Exception:
                final_text = content # Fallback
        else:
            final_text = content # It was already a normal string

        # Step 2: The "Scrubber" - Remove Markdown Backticks
        final_text = final_text.replace("```python", "").replace("```", "").strip()
        
        return final_text

    except ResourceExhausted:
        return "⚠️ **RATE LIMIT HIT:** Please wait 1 minute and try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# 3. Define the Nodes
def analyze_node(state: AgentState):
    """Worker 1: Analyzes COBOL logic."""
    cobol = state['cobol_code']
    prompt = f"""
    You are an expert Mainframe Engineer. Analyze the following COBOL code.
    Explain the business logic, rules, and data structures in simple terms.
    
    COBOL CODE:
    {cobol}
    """
    result = call_gemini_safe(prompt)
    return {"explanation": result}

def translate_node(state: AgentState):
    """Worker 2: Writes the Python code."""
    explanation = state['explanation']
    cobol = state['cobol_code']
    
    # Safety Check
    if "RATE LIMIT HIT" in explanation or "Error" in explanation:
        return {"python_code": "⚠️ Translation paused due to error in previous step."}

    prompt = f"""
    You are a Senior Python Developer. 
    Using the following COBOL code and its explanation, write an equivalent Python script.
    
    IMPORTANT REQUIREMENTS:
    1. Return ONLY the raw Python code. 
    2. Do NOT use Markdown backticks (```).
    3. Use 'from decimal import Decimal' for financial precision.
    4. Use type hinting.
    
    COBOL CODE:
    {cobol}
    
    EXPLANATION:
    {explanation}
    """
    result = call_gemini_safe(prompt)
    return {"python_code": result}

# 4. Build the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("analyze", analyze_node)
workflow.add_node("translate", translate_node)

# Connect nodes
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "translate")
workflow.add_edge("translate", END)

# Compile the app
app = workflow.compile()

def run_agent(cobol_input: str):
    return app.invoke({"cobol_code": cobol_input})
