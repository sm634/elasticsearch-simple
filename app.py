import re
from flask import Flask, render_template, request
from search import Search

app = Flask(__name__)
es = Search()


@app.get('/')
def index():
    return render_template('index.html')

# Implemntation of filter through functions.
def extract_filters(query):
    filters = []

    # category or term filter.
    filter_regex = r'category:([^\s]+)\s*'
    m = re.search(filter_regex, query)
    if m:
        filters.append({
            'term': {
                'category.keyword': {
                    'value': m.group(1)
                }
            },
        })
        query = re.sub(filter_regex, '', query).strip()

    # data filter.
    filter_regex = r'year:([^\s]+)\s*'
    m = re.search(filter_regex, query)
    if m:
        filters.append({
            'range': {
                'updated_at': {
                    'gte': f'{m.group(1)}||/y',
                    'lte': f'{m.group(1)}||/y',
                }
            },
        })
        query = re.sub(filter_regex, '', query).strip()

    return {'filter': filters}, query

#### VECTOR SEARCH ###
# @app.post('/')
# def handle_search():
    
#     query = request.form.get('query', '')
#     filters, parsed_query = extract_filters(query)
#     from_ = request.form.get('from_', type=int, default=0)

#     results = es.search(
#         knn={
#             'field': 'embedding',
#             'query_vector': es.get_embedding(parsed_query),
#             'k': 10,
#             'num_candidates': 50,
#             **filters,
#         },
#         aggs={
#             'category-agg': {
#                 'terms': {
#                     'field': 'category.keyword',
#                 }
#             },
#             'year-agg': {
#                 'date_histogram': {
#                     'field': 'updated_at',
#                     'calendar_interval': 'year',
#                     'format': 'yyyy',
#                 },
#             },
#         },
#         size=5,
#         from_=from_
#     )
#     aggs = {
#         'Category': {
#             bucket['key']: bucket['doc_count']
#             for bucket in results['aggregations']['category-agg']['buckets']
#         },
#         'Year': {
#             bucket['key_as_string']: bucket['doc_count']
#             for bucket in results['aggregations']['year-agg']['buckets']
#             if bucket['doc_count'] > 0
#         },
#     }
#     return render_template('index.html', results=results['hits']['hits'],
#                            query=query, from_=from_,
#                            total=results['hits']['total']['value'], aggs=aggs)


### IMPLENTATION FOR FULL-TEXT SEARCH ###
# @app.post('/')
# def handle_search():
#     query = request.form.get('query', '')
#     filters, parsed_query = extract_filters(query)
#     from_ = request.form.get('from_', type=int, default=0)

#     if parsed_query:
#         search_query = {
#             'must': {
#                 'multi_match': {
#                     'query': parsed_query,
#                     'fields': ['name', 'summary', 'content'],
#                 }
#             }
#         }
#     else:
#         search_query = {
#             'must': {
#                 'match_all': {}
#             }
#         }

#     results = es.search(
#         query={
#             'bool': {
#                 **search_query,
#                 **filters
#             }
#         },
#         aggs={
#             'category-agg': {
#                 'terms': {
#                     'field': 'category.keyword',
#                 }
#             },
#             'year-agg': {
#                 'date_histogram': {
#                     'field': 'updated_at',
#                     'calendar_interval': 'year',
#                     'format': 'yyyy',
#                 },
#             },
#         },
#         size=5,
#         from_=from_
#     )
#     aggs = {
#         'Category': {
#             bucket['key']: bucket['doc_count']
#             for bucket in results['aggregations']['category-agg']['buckets']
#         },
#         'Year': {
#             bucket['key_as_string']: bucket['doc_count']
#             for bucket in results['aggregations']['year-agg']['buckets']
#             if bucket['doc_count'] > 0
#         },
#     }
#     return render_template('index.html', results=results['hits']['hits'],
#                         query=query, from_=from_,
#                         total=results['hits']['total']['value'], aggs=aggs)


### ELSER model used for handling search ###
# @app.post('/')
# def handle_search():
#     """
#     The text_expansion query receives a key with the name of the field to be searched. Under this key, 
#     model_id configures which model to use in the search, and model_text defines what to search for. 
#     Note how in this case there is no need to generate an embedding for the search text, as Elasticsearch manages the model and can take care of that.
#     """
#     query = request.form.get('query', '')
#     filters, parsed_query = extract_filters(query)
#     from_ = request.form.get('from_', type=int, default=0)

#     results = es.search(
#         query={
#             'bool': {
#                 'must': [
#                     {
#                         'text_expansion': {
#                             'elser_embedding': {
#                                 'model_id': '.elser_model_2',
#                                 'model_text': parsed_query,
#                             }
#                         },
#                     }
#                 ],
#                 **filters,
#             }
#         },
#         aggs={
#             'category-agg': {
#                 'terms': {
#                     'field': 'category.keyword',
#                 }
#             },
#             'year-agg': {
#                 'date_histogram': {
#                     'field': 'updated_at',
#                     'calendar_interval': 'year',
#                     'format': 'yyyy',
#                 },
#             },
#         },
#         size=5,
#         from_=from_,
#     )
#     aggs = {
#         'Category': {
#             bucket['key']: bucket['doc_count']
#             for bucket in results['aggregations']['category-agg']['buckets']
#         },
#         'Year': {
#             bucket['key_as_string']: bucket['doc_count']
#             for bucket in results['aggregations']['year-agg']['buckets']
#             if bucket['doc_count'] > 0
#         },
#     }
#     return render_template('index.html', results=results['hits']['hits'],
#                            query=query, from_=from_,
#                            total=results['hits']['total']['value'], aggs=aggs)

### HYBRID SEARCH with sub searches ###
# @app.post('/')
# def handle_search():
#     query = request.form.get('query', '')
#     filters, parsed_query = extract_filters(query)
#     from_ = request.form.get('from_', type=int, default=0)

#     if parsed_query:
#         search_query = {
#             'sub_searches': [
#                 {
#                     'query': {
#                         'bool': {
#                             'must': {
#                                 'multi_match': {
#                                     'query': parsed_query,
#                                     'fields': ['name', 'summary', 'content'],
#                                 }
#                             },
#                             **filters
#                         }
#                     }
#                 },
#                 {
#                     'query': {
#                         'bool': {
#                             'must': [
#                                 {
#                                     'text_expansion': {
#                                         'elser_embedding': {
#                                             'model_id': '.elser_model_2',
#                                             'model_text': parsed_query,
#                                         }
#                                     },
#                                 }
#                             ],
#                             **filters,
#                         }
#                     },
#                 },
#             ],
#             'rank': {
#                 'rrf': {}
#             },
#         }
#     else:
#         search_query = {
#             'query': {
#                 'bool': {
#                     'must': {
#                         'match_all': {}
#                     },
#                     **filters
#                 }
#             }
#         }

#     results = es.search(
#         **search_query,
#         aggs={
#             'category-agg': {
#                 'terms': {
#                     'field': 'category.keyword',
#                 }
#             },
#             'year-agg': {
#                 'date_histogram': {
#                     'field': 'updated_at',
#                     'calendar_interval': 'year',
#                     'format': 'yyyy',
#                 },
#             },
#         },
#         size=3,
#         from_=from_,
#     )
#     aggs = {
#         'Category': {
#             bucket['key']: bucket['doc_count']
#             for bucket in results['aggregations']['category-agg']['buckets']
#         },
#         'Year': {
#             bucket['key_as_string']: bucket['doc_count']
#             for bucket in results['aggregations']['year-agg']['buckets']
#             if bucket['doc_count'] > 0
#         },
#     }
#     return render_template('index.html', results=results['hits']['hits'],
#                            query=query, from_=from_,
#                            total=results['hits']['total']['value'], aggs=aggs)


### HYBRID SEARCH search handler ###
# @app.post('/')
# def handle_search():
#     query = request.form.get('query', '')
#     filters, parsed_query = extract_filters(query)
#     from_ = request.form.get('from_', type=int, default=0)

#     if parsed_query:
#         search_query = {
#             'must': {
#                 'multi_match': {
#                     'query': parsed_query,
#                     'fields': ['name', 'summary', 'content'],
#                 }
#             }
#         }
#     else:
#         search_query = {
#             'must': {
#                 'match_all': {}
#             }
#         }

#     results = es.search(
#         query={
#             'bool': {
#                 **search_query,
#                 **filters
#             }
#         },
#         knn={
#             'field': 'embedding',
#             'query_vector': es.get_embedding(parsed_query),
#             'k': 10,
#             'num_candidates': 50,
#             **filters,
#         },
#         rank={
#             'rrf': {}
#         },
#         aggs={
#             'category-agg': {
#                 'terms': {
#                     'field': 'category.keyword',
#                 }
#             },
#             'year-agg': {
#                 'date_histogram': {
#                     'field': 'updated_at',
#                     'calendar_interval': 'year',
#                     'format': 'yyyy',
#                 },
#             },
#         },
#         size=5,
#         from_=from_,
#     )
#     aggs = {
#         'Category': {
#             bucket['key']: bucket['doc_count']
#             for bucket in results['aggregations']['category-agg']['buckets']
#         },
#         'Year': {
#             bucket['key_as_string']: bucket['doc_count']
#             for bucket in results['aggregations']['year-agg']['buckets']
#             if bucket['doc_count'] > 0
#         },
#     }
#     return render_template('index.html', results=results['hits']['hits'],
#                            query=query, from_=from_,
#                            total=results['hits']['total']['value'], aggs=aggs)


@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    title = document['_source']['name']
    paragraphs = document['_source']['content'].split('\n')
    return render_template('document.html', title=title, paragraphs=paragraphs)

@app.cli.command() #The @app.cli.command() decorator tells the Flask framework to register this function as a custom command, 
# which will be available as flask reindex. The name of the command is taken from the function's name, 
# and the docstring is included here because Flask uses it in the --help documentation.
def reindex():
    """Regenerate the Elasticsearch index."""
    response = es.reindex()
    print(f'Index with {len(response["items"])} documents created.'
          f'in {response["took"]} milliseconds.')

@app.cli.command()
def deploy_elser():
    """Deploy the ELSER v2 model to Elasticsearch."""
    try:
        es.deploy_elser()
    except Exception as exc:
        print(f'Error: {exc}')
    else:
        print(f'ELSER model deployed.')
