from search import Search
import json


es = Search(local=False)
with open('data.json', 'rt') as f:
    documents = json.loads(f.read())

es.insert_documents(documents=documents)
