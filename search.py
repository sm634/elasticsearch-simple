import json
from pprint import pprint
import os
import time

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()


class Search:
    def __init__(self, local=True):
        if local:
            self.es = Elasticsearch('http://localhost:9200')  # <-- connection options need to be added here
        else:
            self.es = Elasticsearch(
                os.environ['ELASTIC_CLOUD_ID'],
                api_key=os.environ['ELASTIC_API_KEY']
                )
        
        client_info = self.es.info()
        print('Connected to Elasticsearch!')
        print(client_info.body)


    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        self.es.indices.create(index='my_documents')
    
    def insert_document(self, document):
        """
        :param document, dict: A document that is represented as k-v pair should be provided. For example:
        document = {
                    'title': 'Work From Home Policy',
                    'contents': 'The purpose of this full-time work-from-home policy is...',
                    'created_on': '2023-11-02',
                }
                response = es.index(index='my_documents', body=document)
                print(response['_id'])
        
        Example method for inserting documents with this method:

        ```
            import json
            from search import Search
            es = Search()
            with open('data.json', 'rt') as f:
                documents = json.loads(f.read())
            for document in documents:
                es.insert_document(document)
        ```
        """
        return self.es.index(index='my_documents', body=document)
    
    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': 'my_documents'}})
            operations.append(document)
        return self.es.bulk(operations=operations)
    
    def reindex(self):
        """
        This method combines the create_index() and insert_documents() methods created earlier, 
        so that with a single call the old index can be destroyed (if it exists) and a new index built and repopulated.
        """
        self.create_index()
        with open('data.json', 'rt') as f:
            documents = json.loads(f.read())
        return self.insert_documents(documents=documents)

    def search(self, **query_args):
        return self.es.search(index='my_documents', **query_args)

    def retrieve_document(self, id):
        return self.es.get(index='my_documents', id=id)
