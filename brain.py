import os
import re
from dotenv import load_dotenv, find_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import ValidationError, SecretStr
from schema import BillingParameters

# 1. Force python to find and load the .env file
load_dotenv(find_dotenv())

# 2. Initialize the Cloud AI (Groq)
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please check your .env file!")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=SecretStr(groq_api_key),
    temperature=0.1  
)

# 3. Set up the Base Parser
base_parser = PydanticOutputParser(pydantic_object=BillingParameters)

# 4. The Strict Prompt
# 4. The Strict Prompt
prompt = PromptTemplate(
    template="""
    You are an automated API that ONLY outputs raw JSON. 
    You DO NOT write Python code. You DO NOT write scripts. You DO NOT explain yourself.
    
    Your job is to read the Current State, read the User Input, and output the updated State as a single JSON object.
    
    Current State: {memory}
    User Input: {input}
    
    {format_instructions}
    
    CRITICAL RULES:
    1. Output ONLY a valid JSON object representing the billing parameters. 
    2. DO NOT output a Python script. No ```python blocks.
    3. If the user input is completely unrelated to electricity billing (e.g., "hello", "how are you", "apple"), output the EXACT same JSON as the Current State without changing a single number.
    """,
    input_variables=["memory", "input"],
    partial_variables={"format_instructions": base_parser.get_format_instructions()}
)
# 5. The Processing Function
def process_user_input(user_input: str, current_memory: dict) -> dict:
    raw_output = None
    
    try:
        # Build the exact prompt string
        _input = prompt.format_prompt(memory=current_memory, input=user_input)
        
        # Get raw response from Groq
        raw_output = llm.invoke(_input.to_string())
        
        # ==========================================
        # GUARANTEE STRING TYPE:
        # Ensure the content is purely a text string before Regex touches it
        # ==========================================
        content = raw_output.content
        if isinstance(content, list):
            content = "".join(str(item) for item in content)
        else:
            content = str(content)
        
        # ==========================================
        # THE FIX: THE "MARKDOWN CLEANER"
        # ==========================================
        if "```json" in content:
            match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                content = match.group(1)
        elif "```" in content:
            match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                content = match.group(1)
                 
        # Clean up any leftover leading/trailing whitespace
        content = content.strip()

        # Parse it safely using the core parser
        parsed_result = base_parser.parse(content)
        
        # Convert back to standard dictionary
        return parsed_result.model_dump()

    except ValidationError as e:
        print(f"Validation Error caught: {e}")
        return current_memory
        
    except Exception as e:
        print(f"System Error: {e}")
        if raw_output:
            print(f"Raw Output was: {raw_output.content}")
        else:
            print("Failed before getting a response from Groq.")
        return current_memory