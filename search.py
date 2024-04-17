import json
from pprint import pprint
import os
import time

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

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
            
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        client_info = self.es.info()
        print('Connected to Elasticsearch!')
        print(client_info.body)

    
    def search(self, **query_args):
        # sub_searches is not currently supported in the client, so we send
        # search requests as raw requests
        if 'from_' in query_args:
            query_args['from'] = query_args['from_']
            del query_args['from_']
        return self.es.perform_request(
            'GET',
            f'/my_documents/_search',
            body=json.dumps(query_args),
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json'},
        )


    ## The following deploy_elser() method in search.py follows a few steps to download and install the ELSER v2 model, 
    ## and to create a pipeline that uses it to populate the elser_embedding field defined above.
    def deploy_elser(self):
        # download ELSER v2
        self.es.ml.put_trained_model(model_id='.elser_model_2',
                                     input={'field_names': ['text_field']})
        
        # wait until ready
        while True:
            status = self.es.ml.get_trained_models(model_id='.elser_model_2',
                                                   include='definition_status')
            if status['trained_model_configs'][0]['fully_defined']:
                # model is ready
                break
            time.sleep(1)

        # deploy the model
        self.es.ml.start_trained_model_deployment(model_id='.elser_model_2')

        # define a pipeline
        self.es.ingest.put_pipeline(
            id='elser-ingest-pipeline',
            processors=[
                {
                    'inference': {
                        'model_id': '.elser_model_2',
                        'input_output': [
                            {
                                'input_field': 'summary',
                                'output_field': 'elser_embedding',
                            }
                        ]
                    }
                }
            ]
        )


    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        self.es.indices.create(
            index='my_documents',
            mappings={
                'properties': {
                    'embedding': {
                        'type': 'dense_vector',
                    },
                    'elser_embedding': {
                        'type': 'sparse_vector',
                    },
                }
            },
            settings={
                'index': {
                    'default_pipeline': 'elser-ingest-pipeline'
                }
            }
        )

    
    def get_embedding(self, text):
        return self.model.encode(text)
    
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
        return self.es.index(index='my_documents', document={
            **document,
            'embedding': self.get_embedding(document['summary'])
        })
    
    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': 'my_documents'}})
            operations.append({
                **document,
                'embedding': self.get_embedding(document['summary'])
                })
            
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
