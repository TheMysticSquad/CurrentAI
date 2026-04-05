import os
import re
from dotenv import load_dotenv, find_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import ValidationError, SecretStr
from schema import BillingParameters
import base64
import PyPDF2
from groq import Groq


# 1. Force python to find and load the .env file
load_dotenv(find_dotenv())

# 2. Initialize the Cloud AI (Groq)

groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found! Add it to Render Environment Variables.")

# --- THE FIX: Use groq_api_key and pass as a plain string ---
llm = ChatGroq(
    groq_api_key=groq_api_key, 
    model_name="llama-3.1-8b-instant", # Note: model_name is the standard param
    temperature=0.1
)
# 3. Set up the Base Parser
base_parser = PydanticOutputParser(pydantic_object=BillingParameters)

# 4. The Agentic Prompt
prompt = PromptTemplate(
    template="""
    You are an intelligent API for a utility billing system. 
    You DO NOT write Python code. You ONLY output raw JSON.
    
    Current State: {memory}
    User Input: {input}
    
    {format_instructions}
    
    CRITICAL AGENT RULES:
    1. Output ONLY a valid JSON object. No markdown code blocks, no explanations.
    2. Review the User Input. If the user lists appliances (like AC, Fan, TV), extract them into the 'appliances' array.
    3. To proceed, the system MUST have: 'category' AND 'load_kw' AND EITHER 'units' OR 'appliances'.
    4. If ANY of those are missing, set "is_complete": false and write a polite "follow_up_message" asking ONLY for the missing details.
    5. If all critical data is present, set "is_complete": true and leave "follow_up_message" empty.
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
    
# ==========================================
# FILE PROCESSING ENGINE (PDF & VISION)
# ==========================================

def extract_text_from_pdf(pdf_file) -> str:
    """Extracts raw text from an uploaded PDF bill."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    extracted_text = ""
    for page in pdf_reader.pages:
        extracted_text += page.extract_text() + "\n"
    return extracted_text

def analyze_image_with_vision(image_file) -> str:
    """Uses Groq's Llama-3.2-Vision to read a meter or paper bill."""
    # Convert the image to base64 so the API can read it
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    vision_prompt = """
    Look at this electricity meter reading or utility bill. 
    Extract the following details if visible:
    1. Total Units Consumed (kWh)
    2. Sanctioned Load (kW)
    3. Category (Domestic or Commercial)
    4. Any Arrears or past unpaid dues
    Return a plain text summary of what you see. Do not calculate anything.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview", # Groq's fast vision model
            temperature=0.2
        )
        content = chat_completion.choices[0].message.content
        return content if content is not None else ""
    except Exception as e:
        return f"Error analyzing image: {e}"
