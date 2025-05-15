# ################################################
# ### This is the server to handle requests to the agents. Request object was added to all endpoints to allow the rate limit library to work
# #################################################
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import asyncio
from contextlib import asynccontextmanager
import pickle
import time
from datetime import date
from redis import Redis
import logfire
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from src.agents.rag_agent import QueryAgent
from src.agents.gemini_agent import UelloSendAgent
from src.utils.manage_db import create_UelloSendAgent_messages_table, fetch_UelloSendAgent_messages
from src.utils.manage_db import create_QueryAgent_messages_table, fetch_QueryAgent_messages


load_dotenv()
logfire.configure(send_to_logfire="if-token-present", scrubbing=False, )


# ################################################
# This is the endpoints for the UelloSendAgent
# #################################################
 

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create lifespan function to start a background task
    """
    asyncio.create_task(cleanup_session())

    await create_UelloSendAgent_messages_table()
    await create_QueryAgent_messages_table()

    print("App is starting...")
    yield
    print("App is shutting down...")

#set global request limit
limiter = Limiter(key_func=get_remote_address, default_limits=["50 per day"])

#Initialize the server
app = FastAPI(title= "UelloSend Support Agent Server", lifespan=lifespan)

#Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = False,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SlowAPIMiddleware)
#Log everything
logfire.instrument_fastapi(app=app, capture_headers=True)


#Schema for requests
class ChatRequest(BaseModel):
    query: str
    session_id: str


#Model for session
class AgentSession:
    def __init__(self, agent: UelloSendAgent):
        self.agent = agent
        self.last_accessed = time.time()


#Create session in memory
sessions: Dict[str, AgentSession] = {}

#Set session timeout, 15 mins in seconds
SESSION_TIMEOUT = 15*60
ADMIN_KEY = os.getenv("ADMIN_KEY")



@app.get("/")
@logfire.instrument()
@limiter.limit("100 per day")
async def root(request: Request):
    """
    Endpoint to check if server is working
    """
    print(f"this is the ip: {get_remote_address(request)}")

    result = {
        'message': 'UelloSend Agent Server 1.0',
        'version': '1.0',
        'date': date.today().strftime('%B %d, %Y'),
    }

    #log data to logfire dashboard
    logfire.info("Sending response", extra={"response_data": result})

    return result



@app.post("/agent/support/chat")
@logfire.instrument()
@limiter.limit("100 per day")
async def chat_support_agent(req: ChatRequest, request: Request):
    """
    Endpoint to handle user support requests that might require tool calling
    """

    session_id = req.session_id

    try:

        #check if session exists
        if session_id not in sessions:
        
            agent = UelloSendAgent()

            sessions[session_id] = AgentSession(agent)
        else:
            sessions[session_id].last_accessed = time.time()

        agent = sessions[session_id].agent

        #run the agent to process request
        response = await agent.run_agent(req.query, session_id)

        res_data = {
        "status": "ok",
        "message": response
        }

        #log data to logfire dashboard
        logfire.info("Sending response", extra={"response_data": res_data})

        return res_data
        
    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in chat support",
            exc_info=e, 
            extra={"session_id": req.session_id, "query": req.query}
        )

        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= "An unexpected internal error occurred. Please try again later."
        )


@app.get("/agent/support/chat/messages/{admin_key}")
@logfire.instrument()
@limiter.limit("100 per day")
async def support_messages(admin_key:str, request: Request):
    """
    Endpoint to retrieve UelloSendAgent chat messages. These are messages that might involved tool calling
    """

    try:
        result = {"status": "ok", "messages": "Unauthorized"}
        if admin_key == ADMIN_KEY:
            data = await fetch_UelloSendAgent_messages()
            
            result = {
                "status": "ok",
                "messages": data
            }

        #log data to logfire dashboard
        logfire.info("Sending response", extra={"response_data_length": len(data)})

        return result
        
    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in fetching support chat messages",
            exc_info=e
        )

        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"An unexpected internal error occurred: {response}"
        )


@app.delete("/agent/sessions/support/{session_id}")
@logfire.instrument()
@limiter.limit("100 per day")
async def delete_uellosend_agent_session(session_id: str, request: Request):
    """
    Function to clean up session of UelloSendAgent that was stored directly in memory
    """

    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail= "Session not found")
        del sessions[session_id]

        result = {
            "status": "ok",
            "message": "Session deleted successfully"
        }

        #log data to logfire dashboard
        logfire.info("Sending response", extra={"response_data": result})

        return result

    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in deleting support agent session from memory",
            exc_info=e
        )

        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"An unexpected internal error occurred: {response}"
        )
    

async def cleanup_session():
    """
    Function to clean up idle sessions that were stored directly in memory
    """
    try:
        while True:
            current_time = time.time()

            session_ids = list(sessions.keys())

            for session_id in session_ids:
                if current_time - sessions[session_id].last_accessed > SESSION_TIMEOUT:
                    del sessions[session_id]

            #Check every 1h
            await asyncio.sleep(3600)
        

    except Exception as e:
        
        logfire.error(
            "Unhandled exception in deleting support agent session from memory",
            exc_info=e
        )



# ################################################
# This is the endpoints for the QueryAgent
# #################################################

#Request Model
class ScrapperRequest(BaseModel):
    urls: List[str]
    admin_key: str


#Create connection to redis
redis_client = Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), db=0, decode_responses=False)


#Set session key for redis
SESSION_PREFIX = "uelloagent_session:"

@logfire.instrument()
async def save_session_to_redis(session_id: str, messages: List[str]):
    """
    Stores QueryAgent message history into redis server
    """
    try:
        serialized_message = pickle.dumps(messages)
        redis_client.setex(
            f"{SESSION_PREFIX}{session_id}",
            SESSION_TIMEOUT,
            serialized_message
        )
        
    except Exception as e:
        logfire.error(
            "Unhandled exception in deleting support agent session from memory",
            exc_info=e
        )


@logfire.instrument()
async def load_messages_from_redis(session_id: str):
    """
    Loads QueryAgent message history from redis server
    """
    try:
        deserialized_message = redis_client.get(f"{SESSION_PREFIX}{session_id}")

        if deserialized_message:
            #Update the session_timeout
            redis_client.expire(
                f"{SESSION_PREFIX}{session_id}",
                SESSION_TIMEOUT
            )

            return pickle.loads(deserialized_message)
        

    except Exception as e:
        logfire.error(
            "Unhandled exception in deleting support agent session from memory",
            exc_info=e
        )
    
    return None


#Endpoint to handle user query requests
@app.post("/agent/query/chat")
@logfire.instrument()
@limiter.limit("100 per day")
async def chat_query_agent(req: ChatRequest, request: Request):
    """
    Endpoint to handle user inquiry requests. These are messages that does not involve tool calling
    """

    try:
        session_id = req.session_id

        #Attempt to load agent
        messages = await load_messages_from_redis(session_id)

        #Create new agent if not found
        if not messages:
        
            messages = []
        

        #run the agent to process request
        agent = QueryAgent(messages)

        response = await agent.generate_response(req.query, session_id)

        #save the updated agent
        await save_session_to_redis(session_id, agent.chat_history)

        res_data = {
            "status": "ok",
            "message": response
        }

        #log data to logfire dashboard
        logfire.info("Sending response", extra={"response_data": res_data})

        return res_data
        

    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in query chat",
            exc_info=e, 
            extra={"session_id": req.session_id, "query": req.query}
        )

        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= "An unexpected internal error occurred. Please try again later."
        )
    


@app.get("/agent/query/chat/messages/{admin_key}")
@logfire.instrument()
@limiter.limit("100 per day")
async def query_messages(admin_key: str, request: Request):
    """
    Endpoint to retrieve QueryAgent chat messages. These are messages that does not involve tool calling
    """

    try:
        result = {"status": "ok", "messages": "Unauthorized"}

        if admin_key == ADMIN_KEY:

            data = await fetch_QueryAgent_messages()
            
            result = {
                "status": "ok",
                "messages": data
            }

        #log data to logfire dashboard
        logfire.info("Sending response", extra={"response_data_length": len(data)})

        return result


    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in fetching query chat messages",
            exc_info=e
        )

        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"An unexpected internal error occurred: {response}"
        )


@app.delete("/agent/sessions/query/{session_id}")
@logfire.instrument()
@limiter.limit("100 per day")
async def delete_query_agent_session(session_id: str, request: Request):
    """
    Function to clean up session of QueryAgent message history that was stored in redis
    """
    try:
        key = f"{SESSION_PREFIX}{session_id}"

        if not redis_client.exists(key) :
            raise HTTPException(status_code=404, detail= "Session not found")
        
        redis_client.delete(key)

        result = {
            "status": "ok",
            "message": "Session deleted successfully"
        }

        #log data to logfire dashboard
        logfire.info("Sending response", extra={"response_data": result})

        return result
        
    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in deleting query agent session from redis",
            exc_info=e
        )

        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"An unexpected internal error occurred: {response}"
        )

 
@app.post("/scraper")
@logfire.instrument()
@limiter.limit("100 per day")
async def scrapper(req: ScrapperRequest, request: Request):
    """
    Endpoint takes a list of urls, scrape the content from the sites and index everything into a vector database
    """

    try:
        res_data = {"status": "ok", "messages": "Unauthorized"}
        if req.admin_key == ADMIN_KEY:

            agent = QueryAgent([])

            docsuments = await agent.scrape_web_content(req.urls)

            result = await agent.embed_and_save_documents(docsuments)

            res_data = {
                "status": "ok",
                "message": result
            }

        #log data to logfire dashboard
        logfire.info("Sending response", extra={"response_data": res_data})

        return res_data
        

    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in scraper",
            exc_info=e
        )

        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"An unexpected internal error occurred: {response}"
        )

