import os
from dotenv import load_dotenv
load_dotenv()
USER_AGENT = os.getenv("USER_AGENT")


from typing import List, Dict
from langchain_community.document_loaders import WebBaseLoader
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from openai import OpenAI

from src.utils.define_system_prompt import RAG_SYSTEM_PROMPT
from src.utils.manage_db import insert_QueryAgent_messages


class QueryAgent:

    def __init__(self, messages):
        self.qdrant_url = os.getenv("QDRANT_HOST")
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION")
        self.embedding_client = HuggingFaceEmbeddings(
                    model_name = os.getenv("HUG_EMBED_MODEL"),
                    model_kwargs={"device": "cpu"}
                )
        self.system_prompt = RAG_SYSTEM_PROMPT
        self.chat_client = OpenAI(
            base_url=os.getenv("OPEN_ROUTER_URL"),
            api_key=os.getenv("OPEN_ROUTER_KEY")
        )
        self.chat_history = messages
        

    async def scrape_web_content(self, url: List[str]) -> List[Document]:
        """
        Web scrapper, uses langchain web loader to scrape website content
        """
        loader = WebBaseLoader(web_path=url)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            add_start_index=True,
            strip_whitespace=True,
            separators=["\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n", "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n", "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\r\n","\n\n\n\n\n\n\n\n\n\n\n\n", "\n\n\n\n\n\n\n\n\n", "\n\n", "\n"] 
        )

        doc = loader.load()

        doc_chunks = text_splitter.split_documents(doc)

        return doc_chunks
    

    async def embed_and_save_documents(self, doc_chunks: List[Document]):
        """
        Embeds and stores embeddings to qdrant vector database
        """
        vector_store = QdrantVectorStore.from_documents(
            documents=doc_chunks,
            embedding=self.embedding_client,
            url = self.qdrant_url,
            collection_name = self.qdrant_collection
        )

        return f"{len(doc_chunks)} documents have been indexed."


    async def retrieve_context(self, query: str):
        """
        Embeds query and then search for semantically similar contents
        """
        vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            embedding=self.embedding_client,
            collection_name=self.qdrant_collection
        )

        results = vector_store.similarity_search(query=query, k=5)

        if results:
            context = []
            
            for res in results:
                data = {
                    "text": res.page_content,
                    "url": res.metadata["source"],
                    "title": res.metadata["title"]
                    
                }

                context.append(data)

            return context
        return None
    
    async def generate_response(self, query: str, session_id: str):
        """
        Main function that combines everything in this class to generate responses.
        uses free model from OPEN ROUTER and OpenAI API to interact with LLM
        """

        #Check for first time agent call so that system prompt can be added to the message
        if len(self.chat_history) == 0:
            self.chat_history.append({
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": self.system_prompt
                    }
                ]
            })

            self.chat_history.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": query
                    }
                    ]
                })

            await insert_QueryAgent_messages(session_id, "user", query)


            res_message = await self.generater(session_id= session_id)
            

            return res_message


        contexts = await self.retrieve_context(query)

        #If contextual information is found
        if contexts:

            # Construct prompt with retrieved contexts
            prompt = f"""Answer the following question based on the provided context information. If the answer cannot be found in the context, say "I don't have enough information to answer this question."

            Context information:
            {chr(10).join([f"[{i+1}] {ctx['text']} (Source: {ctx['title']} - {ctx['url']})" for i, ctx in enumerate(contexts)])}

            Question: {query}

            Answer:"""

            self.chat_history.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                    ]
                })
            
            await insert_QueryAgent_messages(session_id, "user", prompt)

            res_message = await self.generater(session_id=session_id)

            return res_message
        

        #If no contextual information found
        res_message = f"Unable to respond to the query: {query}."
        
        await insert_QueryAgent_messages(session_id, "model", res_message)

        return res_message
    


    async def generater(self, session_id):
        """
        Generates responses uses free model from OPEN ROUTER and OpenAI API to interact with LLM
        """

        responses = self.chat_client.chat.completions.create(
                extra_body={},
                model=os.getenv("OPEN_ROUTER_MODEL"),
                messages=self.chat_history,
                temperature=0.2,
                seed=23
            )
        
        self.chat_history.append(responses.choices[0].message)

        res_message = responses.choices[0].message.content
        #print(f"response - {res_message}")
        await insert_QueryAgent_messages(session_id, "model", res_message)

        return res_message
        