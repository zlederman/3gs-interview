from typing import Callable
import pytest
from langchain_community.graphs.graph_document import GraphDocument, Node, Document, Relationship
from faker import Faker
from functools import wraps
from src.wikidata import populate_from_wikidata

@pytest.fixture
def faker() -> Faker:
    return Faker("en_US")

@pytest.fixture
def make_graph_node(faker: Faker):
    def wrapped() -> Node:
        return Node(
            id=faker.city(),
            type="city",
            properties={}
        )
    return wrapped

@pytest.fixture
def make_graph_document(make_graph_node: Callable[[], Node]) -> Callable[[], GraphDocument]:
    def wrapped():
        return GraphDocument(
            nodes=[make_graph_node() for _ in range(12)], 
            relationships=[Relationship(source=make_graph_node(),target=make_graph_node(), type="FAKED_REL")], 
            source=Document("hello world")
        )
    return wrapped

@pytest.mark.asyncio
async def test_basic_graph_document(make_graph_document: Callable[[], GraphDocument]):
    graph_docs = [make_graph_document() for _ in range(3)]
    modified = await populate_from_wikidata(graph_docs)
    for graph_doc in modified:
        for node in graph_doc.nodes:
            assert "__qid__" in node.properties
        
