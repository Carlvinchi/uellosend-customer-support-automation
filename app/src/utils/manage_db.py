####
# Defines helper functions to manage database for storing messages
####

import os
from dotenv import load_dotenv
import sqlite3
import logfire

load_dotenv()
logfire.configure(send_to_logfire="if-token-present", scrubbing=False, )

####
# UelloSendAgent Database Functions
####

async def create_UelloSendAgent_messages_table():
    """
    Creates the database to be used to store UelloSendAgent chat messages.
    """
    try:
        conn = sqlite3.connect(f"{os.getenv('UELLOSEND_AGENT_DB')}.db")

        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS messages(
                    message_id INTEGER PRIMARY KEY,
                    message_session_id VARCHAR(120) NOT NULL,
                    message_role CHAR(10) NOT NULL,
                    message_text TEXT NOT NULL,
                    agent CHAR(20) DEFAULT ('UelloSendAgent'),
                    created_at TEXT DEFAULT (datetime('now'))
            );
        """)

        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in UelloSendAgent table",
            exc_info=e, 
            extra={"info": response}
        )

    return True # I am returning true because the system does not require the database aspect to function
    


async def insert_UelloSendAgent_messages(message_session_id, message_role, message_text):
    """
    Insert chat messages into the UelloSendAgent database.
    """
    try:
        conn = sqlite3.connect(f"{os.getenv('UELLOSEND_AGENT_DB')}.db")

        cursor = conn.cursor()

        cursor.execute("INSERT INTO messages(message_session_id, message_role, message_text) VALUES(?, ?, ?)",
                    (message_session_id, message_role, message_text))

        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in insert UelloSendAgent messages",
            exc_info=e, 
            extra={"info": response}
        )

    return True # I am returning true because the system does not require the database aspect to function


async def fetch_UelloSendAgent_messages():
    """
    Retrieves chat messages from the UelloSendAgent database.
    """
    try:
        conn = sqlite3.connect(f"{os.getenv('UELLOSEND_AGENT_DB')}.db")

        cursor = conn.cursor()

        cursor.execute("""SELECT * FROM messages ORDER BY message_id DESC ;""")
        result = cursor.fetchall()

        conn.commit()
        cursor.close()
        conn.close()

        return result
    
    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in fetch UelloSendAgent messages",
            exc_info=e, 
            extra={"info": response}
        )
        raise Exception(response)


####
# QueryAgent Database Functions
####

async def create_QueryAgent_messages_table():
    """
    Creates the database to be used to store QueryAgent chat messages.
    """
    try:
        conn = sqlite3.connect(f"{os.getenv('QUERY_AGENT_DB')}.db")

        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS messages(
                    message_id INTEGER PRIMARY KEY,
                    message_session_id VARCHAR(120) NOT NULL,
                    message_role CHAR(10) NOT NULL,
                    message_text TEXT NOT NULL,
                    agent CHAR(20) DEFAULT ('QueryAgent'),
                    created_at TEXT DEFAULT (datetime('now'))
            );
        """)

        conn.commit()
        cursor.close()
        conn.close()


    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in create QueryAgent table",
            exc_info=e, 
            extra={"info": response}
        )

    return True # I am returning true because the system does not require the database aspect to function


async def insert_QueryAgent_messages(message_session_id, message_role, message_text):
    """
    Insert chat messages into the QueryAgent database.
    """

    try:
        conn = sqlite3.connect(f"{os.getenv('QUERY_AGENT_DB')}.db")

        cursor = conn.cursor()

        cursor.execute("INSERT INTO messages(message_session_id, message_role, message_text) VALUES(?, ?, ?)",
                    (message_session_id, message_role, message_text))

        conn.commit()
        cursor.close()
        conn.close()


    except Exception as e:
        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in insert QueryAgent messages",
            exc_info=e, 
            extra={"info": response}
        )

    return True # I am returning true because the system does not require the database aspect to function



async def fetch_QueryAgent_messages():
    """
    Retrieves chat messages from the QueryAgent database.
    """
    try:
        conn = sqlite3.connect(f"{os.getenv('QUERY_AGENT_DB')}.db")

        cursor = conn.cursor()

        cursor.execute("""SELECT * FROM messages ORDER BY message_id DESC;""")
        result = cursor.fetchall()

        conn.commit()
        cursor.close()
        conn.close()

        return result

    except Exception as e:

        response = f"Error - {str(e)}"

        logfire.error(
            "Unhandled exception in fetch QueryAgent messages",
            exc_info=e, 
            extra={"info": response}
        )
        raise Exception(response)

    