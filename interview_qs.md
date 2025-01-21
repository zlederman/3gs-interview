# Neo4j RAG Tool Interview Questions and Analysis


## 0. Start by forking and deploying the application locally. You'll need an LLM API key to get it to work - let me know if you need me to generate one for you. You'll also need an AuraDB instance. You should be able to deploy one for free, but you can let me know if you're having issues with that part.

## 1. Where in the repository is the NER logic? Describe it. How would you enhance it to include more features for each entity? Can you write a function to evaluate named entities against entities in Wikidata?
### Where in the repository is the NER logic? Describe it.
NER is Named Entity Recognition which is essentially the process of extracting structured data from unstructured data sources. In this code base the NER logic is located in `backend/src/shared/schema_extraction.py`

It essentially takes a chunk of input text, a prompt and asks an llm to extract structured data from the text using the prompt. There are two types of prompts but all of the callers for this function `schema_extraction_from_text` enforce the schema. 

The operation utilizes a langchain structured output module, and a pydantic model called Schema which represents the target Graph structure. Once its run on the input text it outputs the matching json model

### Can you write a function to evaluate named entities against entities in Wikidata?


## 2. Where in the repository is the RAG retrieval logic? What property is the LLM querying, and how is that property generated?

### To RAG you must first index
The RAG Logic starts with the `/extract` http endpoint. This endpoint consumes a datasource, in our case wikipedia pages, and then proceeds to the `processing_source` function. This function is like the high level orchestrator of the extraction process and creates the graph, puts a vector index on the graph, chunks from data, and associates new chunks with existing chunks in the vector database associated with cosine similarity.

### Retrieval 
Inside of score.py there is an endpoint called `/chat_bot` this is where all of the RAG work happens. It starts by sending the function `QA_RAG` to a worker thread. This function then goes to the `/process_chat_response` which sets up the retriever module, gets the llm, and the model version. The retriever is a `Neo4jVector`retriever from `langchain_neo4j`. This is the config:
```
def create_retriever(neo_db, document_names, chat_mode_settings,search_k, score_threshold):
    if document_names and chat_mode_settings["document_filter"]:
        retriever = neo_db.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                'k': search_k,
                'score_threshold': score_threshold,
                'filter': {'fileName': {'$in': document_names}}
            }
        )
        logging.info(f"Successfully created retriever with search_k={search_k}, score_threshold={score_threshold} for documents {document_names}")
    else:
        retriever = neo_db.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={'k': search_k, 'score_threshold': score_threshold}
        )
        logging.info(f"Successfully created retriever with search_k={search_k}, score_threshold={score_threshold}")
    return retriever
```

It essentially just does top k search using the cosine similarity of an embedded query and the embedded nodes in the neo4j db. 

It then retrieves the documents here:
```
docs = doc_retriever.invoke({"messages": messages},{"callbacks":[handler]})
```
## 3. What does the application use for the frontend?  

Language: Typescript
UI Framework: React
CSS Framework: Tailwind
Packaging and Deploys: Vite
Server: Nginx
Component Library: Neo4j-NDL 
Containerization: Docker



## 4. Finally, can you give me an assessment of what you think of the application? Include things you like, and things you don't like

To be completely honest, this app looks like a ton of tech debt. Having audited the backend the most I feel I can give you an accurate critique of why I think this should not be used.

### Backend Service
#### 1. FastAPI
- Not using native dependency injection, instead creates connections at request time
-
- Not using pydantic schemas which allow for rapid documentation and better IDE experience
- Not using routers, resources all are at the top level domain
- Database connections are passed from front end to backend
- Using forms instead of POST requests

#### 2. Architecture and Project Structure
- Poor file naming: e.g. all server routes are defined in score.py, main.py isn't the main file
- Server routes aren't put into seperate folders which indicate which REST resource they are using
- Repo isn't organized well. Very flat file heirarchy, more nesting could provide more context on what code is related.
- Massive functions everywhere, 30+ lines! Refer to `processing_source` in main.py
- Missing type annotations and passing around raw dicts
- Not using python moduling system with `__init__.py`
- Not using a proper python project management tool (uv, poetry, pipenv), instead relies on static requirements.txt
- Ingestion pipelines aren't organized into stages just functions calling other functions, fairly confusing and deep call heirarchies
- Using threadpooling over background tasks.
- Environment variables can causes crashes mid execution instead of crashing on startup. See `llm.py -> get_llm()`  
- Environment variables are overly complex and have parsing needs such as passing llm key and model id in the same env var, see `LLM_MODEL_CONFIG_openai_gpt_3.5`
- Missing an in depth extraction diagram and documentation

#### 3. Testing
- Not using a testing framework like unittest or pytest
- Not given a dedicated testing folder


#### 4. LLMs
- I am not a fan of langchain. Its really hard to debug and uses overly complex call back functions and uses some bespoke pipe operator overloading which looks pretty but gets complex fast.
 



