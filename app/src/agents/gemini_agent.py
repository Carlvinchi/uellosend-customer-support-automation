####
# This is where the agent class is defined 
####

import os
from dotenv import load_dotenv
from google import generativeai as genai
from google.generativeai import types
import uuid
from typing import Dict, Callable


from src.utils.define_tools import TOOLS_SCHEMA
from src.utils.define_system_prompt import SYSTEM_PROMPT
from src.tools.tool_set import verify_customer_exist, fix_credit_topup_issue, resend_account_verification_link, send_password_reset_link
from src.utils.manage_db import insert_UelloSendAgent_messages

load_dotenv()

class UelloSendAgent:
    def __init__(self):
        self.model = os.getenv("GEMINI_MODEL")
        self.system_prompt = SYSTEM_PROMPT
        self.available_tools = self._register_tools()
        self.config_tools = types.Tool(function_declarations=TOOLS_SCHEMA)
        self.conversation = self._init_conversation_client()
        self.chat_history = {}


    def _register_tools(self) -> Dict:
        """
        Registers all the tools available to the agent
        """
        available_tools = {}
        available_tools["verify_customer_exist"] = {
            "name": "verify_customer_exist",
            "function": verify_customer_exist
        }

        available_tools["fix_credit_topup_issue"] = {
            "name": "fix_credit_topup_issue",
            "function": fix_credit_topup_issue
        }

        available_tools["resend_account_verification_link"] = {
            "name": "resend_account_verification_link",
            "function": resend_account_verification_link
        }

        available_tools["send_password_reset_link"] = {
            "name": "send_password_reset_link",
            "function": send_password_reset_link
        }

        return available_tools


    def _init_conversation_client(self):
        """
        Initializes the chat client to be used by the agent
        """
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        client = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=self.system_prompt,
            tools=self.config_tools
        )

        conversation = client.start_chat()

        return conversation
    

    async def execute_functions(self, function_to_call: Callable, func_args, func_name: str) -> Dict:
        """
        Executes functions called by the agent
        """
        
        try:
            function_response = function_to_call(**func_args)
            
            # Send tool result back to the model
            
            rs=f"Tool called: {func_name} and result is: {function_response}"
            tool_response = {
                "parts": rs
            }

        except Exception as e:

            rs=f"Tool called: {func_name} and result is: Error - {str(e)}"
            tool_response = {
                "parts": rs
            }

        return tool_response
    

    async def run_agent(self, user_prompt: str, session_id: str):
        """
        Main function that combines everything in this class to generate responses.
        uses Google Gemini model and google-generativeai API to interact with LLM
        """
        
        await insert_UelloSendAgent_messages(session_id, "user", user_prompt)
        responses = self.conversation.send_message(user_prompt)
        
        
        # Process function calls made by the model
        responses_list = []
        responses_list.append(responses)

        while responses_list:

            tool_calls = responses.candidates[0].content.parts

            
            for part in tool_calls:

                if part.function_call.name:
                    func_name = part.function_call.name
                    function_to_call = self.available_tools[func_name]
                    func_args = part.function_call.args
                
                    print(f"Tool called: {func_name}")


                    ms = f"Tool called: {func_name}"
                    await insert_UelloSendAgent_messages(session_id, "model", ms)

                    tool_response = await self.execute_functions(function_to_call["function"], func_args, func_name)
                    await insert_UelloSendAgent_messages(session_id, "tool", str(tool_response))


                    #Send tool call response to the agent
                    responses = self.conversation.send_message(tool_response)
                    await insert_UelloSendAgent_messages(session_id, "model", responses.text)

            #remove response from list        
            responses_list.pop(0)


        await insert_UelloSendAgent_messages(session_id, "model", responses.text)
        return responses.text


    async def create_new_chat(self):
        """Create a new chat and return its ID for later retrieval"""
        chat_id = str(uuid.uuid4())
        
        self.chat_history[chat_id] = {
            "chat_id": chat_id
        }

        return chat_id


    async def return_chat_history(self):
        """Returns the chat history """
        return self.conversation.history

