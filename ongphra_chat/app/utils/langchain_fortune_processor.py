from typing import Dict, Any, List, Optional
import logging
import re
from datetime import datetime

from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.schema import OutputParserException
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI

from app.config.settings import get_settings
from app.utils.fortune_tool import fortune_calculator, calculate_fortune
from app.utils.tool_handler import ToolResult

logger = logging.getLogger(__name__)
settings = get_settings()

# Define tools available to the agent
tools = [
    Tool(
        name="calculate_fortune",
        func=fortune_calculator,
        description="Calculate fortune based on birthdate in format YYYY-MM-DD"
    )
]

# Create a prompt template for the agent
fortune_agent_template = """You are a Thai fortune teller specializing in 7-base-9 numerology (Lekjet-Faan-Gao).

Your task is to analyze and interpret fortune data from birthdates using authentic 7-base-9 principles. Each interpretation should be:
1. Driven solely by the actual numerical data
2. Unique to the specific person's birth numbers
3. Personalized and conversational
4. Based on detailed analysis, not generic statements

You have access to the following tools:

{tools}

Use the following format:

User: <user question>
Thought: <your thoughts about what to do>
Action: <tool name>
Action Input: <tool input>
Observation: <tool output>
Thought: <your thoughts about the observation>
Action: <tool name or "Final Answer">
Action Input: <tool input or final answer>

Begin!

User: {input}
Thought:"""

agent_prompt = PromptTemplate.from_template(fortune_agent_template)

# Create OpenAI language model
llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0.2,
)

# Create the agent
agent = create_react_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    handle_parsing_errors=True,
    verbose=True
)

async def process_fortune_request(message: str, lang: str = "thai") -> ToolResult:
    """Process a fortune request using LangChain's agent system.
    
    Args:
        message: The user message that may contain birthdate information
        lang: The language to respond in (default: "thai")
        
    Returns:
        ToolResult containing the fortune interpretation or a prompt for birthdate
    """
    # Check if message contains a birthdate
    date_pattern = r"(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{4})"
    date_match = re.search(date_pattern, message)
    
    if date_match:
        birthdate_str = date_match.group(0)
        
        # Convert DD/MM/YYYY to YYYY-MM-DD if needed
        if '/' in birthdate_str:
            parts = birthdate_str.split('/')
            if len(parts) == 3 and len(parts[2]) == 4:  # Format is DD/MM/YYYY
                birthdate_str = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        
        try:
            # Run the agent to get a complete fortune interpretation
            agent_input = f"Generate a data-driven fortune interpretation for birthdate {birthdate_str}"
            if lang == "english":
                agent_input += " in English language"
            else:
                agent_input += " in Thai language"
                
            result = await agent_executor.ainvoke({"input": agent_input})
            
            # Extract the final answer
            response = result.get("output", "")
            
            # Calculate fortune data for the response
            fortune_data = calculate_fortune(birthdate_str)
            
            return ToolResult(
                success=True,
                handled=True,
                response=response,
                data={
                    "birthdate": birthdate_str,
                    "fortune_data": fortune_data,
                    "langchain_result": result
                }
            )
        except Exception as e:
            logger.error(f"Error in LangChain fortune processing: {str(e)}")
            
            # Generate error response based on language without hardcoded text
            error_msg = ""
            if lang == "english":
                error_msg = f"I'm unable to process your fortune data at this moment: {str(e)}"
            else:
                error_msg = f"ขณะนี้ฉันไม่สามารถประมวลผลข้อมูลดวงชะตาของคุณได้: {str(e)}"
                
            return ToolResult(
                success=False,
                handled=True,
                error=str(e),
                response=error_msg
            )
    else:
        # Use LangChain to generate a natural-sounding request for birthdate
        try:
            # Generate a request for birthdate based on language
            agent_input = "Ask user for their birthdate information in natural language"
            if lang == "english":
                agent_input += " in English"
            else:
                agent_input += " in Thai"
                
            result = await agent_executor.ainvoke({"input": agent_input})
            response = result.get("output", "")
            
            # If no response was generated, use a simple fallback
            if not response:
                if lang == "english":
                    response = "To generate your fortune reading, I need your birthdate in YYYY-MM-DD format."
                else:
                    response = "เพื่อทำนายดวงชะตาของคุณ ฉันต้องการทราบวันเกิดในรูปแบบ ปี-เดือน-วัน (เช่น 1990-05-15)"
            
            return ToolResult(
                success=True,
                handled=True,
                response=response,
                data={"context": "fortune_request_birthdate"}
            )
        except Exception as e:
            logger.error(f"Error generating birthdate request: {str(e)}")
            
            # Simple fallback
            if lang == "english":
                response = "Please share your birthdate for a fortune reading."
            else:
                response = "กรุณาบอกวันเกิดของคุณเพื่อการทำนายดวงชะตา"
                
            return ToolResult(
                success=True,
                handled=True,
                response=response,
                data={"context": "fortune_request_birthdate"}
            ) 