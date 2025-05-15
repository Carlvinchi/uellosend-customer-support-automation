# Customer Support Automation With UelloSend AI Agents

The project provided me an opportunity to put everything I learned as an AI Intern at Dataphyte UK to use. 

This is a full production grade application, and we are making the full code  available for other learners. 

Any learner who carefully explores the code will have basic understanding and implementation of concepts like 
 - Retrieval-Augmented Generation
 - Building AI Agents with no framework
 - Using LLM APIs (OpenAI and Google GenerativeAI SDK)
 - Building REST server with FastAPI
 - Implement Rate Limiting
 - Logging
 - Error handling
 - Using docker

Learners must use resources available on the internet to better understand the concepts used in this project.

### Highlevel Overview 

The system is made of two agents:

**UelloSendAgent**

- Functionality: This agent  is designed for task execution and process automation. It utilizes Gemini Large Language Model (LLM) augmented with a defined set of tools and capabilities, accessed via robust API integrations or function calling mechanisms.
  
- Core Responsibilities: It directly interacts with the UelloSend platform's backend systems (via dedicated APIs) to fulfill specific, action-oriented customer requests. Key examples include:
  - Initiating and managing password reset workflows.
  - Executing account verification procedures.
  - Diagnosing and resolving discrepancies or failures in credit top-up transactions.

- This agent was developed using Google Generative AI SDK

**QueryAgent**

- Functionality: This agent specializes in providing informative responses to user enquiries. It is powered by Llama 4 Large Language Model (LLM) integrated within a Retrieval-Augmented Generation (RAG) pipeline, which is composed of embedding, searching, and generation.
  
- Core Responsibilities: Addresses "how-to" questions, policy clarifications, and general information requests by retrieving relevant information from a dedicated knowledge base and synthesizing accurate, context-aware answers (source: uellosend.com).
  
- Underlying Mechanisms: The RAG pipeline typically involves:
  - Ingestion Service: Processing and indexing UelloSend documentation, FAQs, and support articles into a searchable format (e.g., a vector database potentially hosted as its own service).
  - Retrieval Service: Embedding user queries and performing semantic similarity searches against the indexed knowledge base.
  - Generation Service: Feeding the retrieved context along with the original query to the LLM to generate a coherent and informative response.

- This agent was developed using  OpenAI SDK and OpenRouter API.

**Other Details**

- The two agents are exposed to clients via FastAPI server endpoints. The FastAPI server has rate limit implemented using slowapi package

- A simple frontend has been developed to consume the APIs, headover to uellosend.com to try it out. Locate the floating button on the site and start chatting.

- The implementation uses both system memory and redis to maintain stateful interactions between client and server.

- Pydantic logfire is used to log all server usage information

- The whole system was developed using microservice architecture and deployed using docker on a vm on uvitechcloud.com.


**Agents in Action**
This is the frontend for consuming the backend
![Simple Frontned](./images/index.png)

Clicking on the chat widget
![Clicking the chat button](./images/open_window.png)

The QueryAgent introducing itself
![QueryAgent Intro](./images/queryAgent_intro.png)

The QueryAgent responding to a query
![Respond to query](./images/queryagent_response.png)

The UelloSendAgent introducing itself
![UelloSendAgent Intro](./images/SupportAgent_intro.png)

The UelloSendAgent responding to user
![Response 1](./images/SupportAgent_resp_1.png)

The UelloSendAgent responding to user
![Response 2](./images/SupportAgent_resp_2.png)

##### Setup Instructions

- use .env file if you will not use docker // You can populate some fields with dummy data
  
- use .prod.env file if you will use docker // You can populate some fields with dummy data

- run docker compose up -d to build and run containers for first time deployment

- for subsequent deployments use

- docker compose build --no-cache to build without using cached data

- docker compose up to start the services

**Conclusion**: The UelloSend AI agents, designed with a microservice modular architecture and deployed using Docker running on UviTech Cloud Services (UCS), represents a robust, scalable, and maintainable solution for intelligent customer support automation.


**Credits**

- Dr. Boamah Kojo Opoku

- Confidence Antwi Boasiako

By ~ *Carlvinchi*

ENJOY!!