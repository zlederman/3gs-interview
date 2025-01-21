import asyncio
from wikidata.client import Client
from langchain_community.graphs.graph_document import GraphDocument, Node
import aiohttp
from typing import List, Optional

async def search_wikidata(label: str, session: aiohttp.ClientSession) -> Optional[str]:
    '''
    using an async http client fire off an async entity search to the wikidata api
    returns:
        the qid of the node id | None
    '''
    url = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'language': 'en',
        'search': label
    }
    async with session.get(url=url, params=params) as response:
        data = await response.json()
        if data['search']:
            return data['search'][0]['id']
    return None



async def get_qids(graph_doc: GraphDocument) -> List[str]:
    '''
    runs a fan out operation for all nodes in a graph document 
    returns:
        list[qid]
    '''
    async with aiohttp.ClientSession() as session:
        tasks = [search_wikidata(node.id, session) for node in graph_doc.nodes]
        results = await asyncio.gather(*tasks)
        return results

async def populate_from_wikidata(graph_docs: List[GraphDocument]) -> List[GraphDocument]:
    '''
    loops through every graph document, gets the qids and 
    then assigns them to the relevant node property field
    returns:
        the modified GraphDocuments
    '''
    for graph_doc in graph_docs:
        qids = await get_qids(graph_doc)
        for i, node in enumerate(graph_doc.nodes):
            node.properties["__qid__"] = qids[i]
    return graph_docs
            
