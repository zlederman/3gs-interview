# Neo4j RAG Tool Interview Questions and Analysis


## 0. Start by forking and deploying the application locally. You'll need an LLM API key to get it to work - let me know if you need me to generate one for you. You'll also need an AuraDB instance. You should be able to deploy one for free, but you can let me know if you're having issues with that part.

## 1. Where in the repository is the NER logic? Describe it. How would you enhance it to include more features for each entity? Can you write a function to evaluate named entities against entities in Wikidata?
### Where in the repository is the NER logic? Describe it.
NER is Named Entity Recognition which is essentially the process of extracting structured data from unstructured data sources.



After reviewing the code I found where the core NER extraction occurs. 
The call heirarchy is as follows
```
[HTTP request to /extract endpoint]
    -> [extract_graph_from_file_Wikipedia]
            -> [processing_source]
                    -> [processing_chunks]
                        -> [get_graph_from_llm]
                            -> [get_graph_document_list]
                                -> [llm_transformer.convert_to_graph_documents]
```
The core functionality is implemented by langchain  `LLMGraphTransformer`. Essentially it passes a chunk of text to a prompt, the allowed named entities, the allowed relationship types and then populates a series of nodes and relationships from those chunks. The `LLMGraphTransformer` uses a chain which is defined simply as `prompt | llm`

this is the prompt that underlies the extraction functionality:
```
system_prompt = (
    "# Knowledge Graph Instructions for GPT-4\n"
    "## 1. Overview\n"
    "You are a top-tier algorithm designed for extracting information in structured "
    "formats to build a knowledge graph.\n"
    "Try to capture as much information from the text as possible without "
    "sacrificing accuracy. Do not add any information that is not explicitly "
    "mentioned in the text.\n"
    "- **Nodes** represent entities and concepts.\n"
    "- The aim is to achieve simplicity and clarity in the knowledge graph, making it\n"
    "accessible for a vast audience.\n"
    "## 2. Labeling Nodes\n"
    "- **Consistency**: Ensure you use available types for node labels.\n"
    "Ensure you use basic or elementary types for node labels.\n"
    "- For example, when you identify an entity representing a person, "
    "always label it as **'person'**. Avoid using more specific terms "
    "like 'mathematician' or 'scientist'."
    "- **Node IDs**: Never utilize integers as node IDs. Node IDs should be "
    "names or human-readable identifiers found in the text.\n"
    "- **Relationships** represent connections between entities or concepts.\n"
    "Ensure consistency and generality in relationship types when constructing "
    "knowledge graphs. Instead of using specific and momentary types "
    "such as 'BECAME_PROFESSOR', use more general and timeless relationship types "
    "like 'PROFESSOR'. Make sure to use general and timeless relationship types!\n"
    "## 3. Coreference Resolution\n"
    "- **Maintain Entity Consistency**: When extracting entities, it's vital to "
    "ensure consistency.\n"
    'If an entity, such as "John Doe", is mentioned multiple times in the text '
    'but is referred to by different names or pronouns (e.g., "Joe", "he"),'
    "always use the most complete identifier for that entity throughout the "
    'knowledge graph. In this example, use "John Doe" as the entity ID.\n'
    "Remember, the knowledge graph should be coherent and easily understandable, "
    "so maintaining consistency in entity references is crucial.\n"
    "## 4. Strict Compliance\n"
    "Adhere to the rules strictly. Non-compliance will result in termination."
)
```

Using this prompt we can extract a unique set of Nodes and Relationships on those nodes. 


### Can you write a function to evaluate named entities against entities in Wikidata?
Yes, I started by researching what an entity in wikidata is represented by. An entity in Wikidata is represented by a Q-Identifier and relationships are represented by their P-Identifiers. Since we are just working with nodes, my goal was to create a function that populated each node with a respective Q-Identifier, denoted as `__qid__`. 

My first step was identifing where we can send in a piece of text and retrieve a Q-Identifier back. After looking around this is the endpoint and params:
```
url = 'https://www.wikidata.org/w/api.php'
params = {
    'action': 'wbsearchentities',
    'format': 'json',
    'language': 'en',
    'search': label
}
```

After that I used what I learned from part A, which is that NER objects are represented as GraphDocuments with collections of extracted nodes and collections of extracted relationships. I used this information to take the output of `get_graph_from_llm` from `processing_chunks` which is a `List[GraphDocument]`. I then wrote a function that concurrently fires off requests to the wikidata api for each node in each graph document. This can be seen in `backend/src/wikidata.py`. After that I wrote a simple test to confirm functionality which you can see in `backend/test_wikidata.py`
## 2. Where in the repository is the RAG retrieval logic? What property is the LLM querying, and how is that property generated?

### To RAG you must first index
The RAG Logic starts with the `/extract` http endpoint. This endpoint consumes a datasource, in our case wikipedia pages, and then proceeds to the `processing_source` function. This function is like the high level orchestrator of the extraction process and creates the graph, puts a vector index on the graph,  and associates new chunks with existing chunks in the vector database associated with cosine similarity.

### Retrieval 
Inside of score.py there is an endpoint called `/chat_bot` this is where the RAG work happens. It starts by sending the function `QA_RAG` to a worker thread. This function then goes to the `/process_chat_response` which sets up the retriever module, gets the llm, and the model version. The retriever is a `Neo4jVector`retriever from `langchain_neo4j`. This is the config:
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

To be completely honest, the backend could use some reorganization. Its kind of hard to follow a lot of the execution flow and there are some very opaque graph queries which could be documented better. I would also like to see a summary of the techniques used to improve the LLM performance and keep extraction clean.

### Backend Service
#### 1. FastAPI
- Not using native dependency injection, instead creates connections at request time
- Not using pydantic schemas which allow for rapid documentation and better IDE experience
- Not using routers, resources all are at the top level domain
- Database connections are passed from front end to backend
- Using forms instead of json requests, I prefer jsons because they are easier to work with and FastAPI makes documenting and annotating a breeze

#### 2. Architecture and Project Structure
- Poor file naming: e.g. all server routes are defined in score.py, main.py isn't the main file
- Server routes aren't put into seperate folders which indicate which REST resource they are using
- Repo isn't organized well. Very flat file heirarchy, more nesting could provide more context on what code is related.
- Massive functions everywhere, 30+ lines! See `processing_source` in main.py
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
- I am not a fan of langchain. Its really hard to debug and uses overly complex call back functions and a pipe operator overloading which looks pretty but gets complex fast.
 



