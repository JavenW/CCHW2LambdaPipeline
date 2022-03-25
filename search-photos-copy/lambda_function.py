import json
import boto3
import requests

def lex2_disambiguate(send_message):
     # Define the client to interact with Lex
    client = boto3.client('lexv2-runtime', region_name='us-east-1')
    
    response = client.recognize_text(
        botId='J1KQWOMJRX',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId="test_session",
        text=send_message)
        
    print("response: ", response)
    
    content = response['messages'][0]['content']
    
    if content == "Please show me some keywords you want to see." or content == "i am still learning what you said', 'please come back later.":
        return []
    
    msg_from_lex = content.split(", ")
    keywork_list = [x.strip().lower() for x in msg_from_lex]
    
    
    SINGULAR_UNINFLECTED = ['gas', 'asbestos', 'womens', 'childrens', 'sales', 'physics']

    SINGULAR_SUFFIX = [
        ('people', 'person'),
        ('men', 'man'),
        ('wives', 'wife'),
        ('menus', 'menu'),
        ('us', 'us'),
        ('ss', 'ss'),
        ('is', 'is'),
        ("'s", "'s"),
        ('ies', 'y'),
        ('ies', 'y'),
        ('hes', 'h'),
        ('es', 'e'),
        ('s', '')
    ]
    def singularize_word(word):
        for ending in SINGULAR_UNINFLECTED:
            if word.lower().endswith(ending):
                return word
        for suffix, singular_suffix in SINGULAR_SUFFIX:
            if word.endswith(suffix):
                return word[:-len(suffix)] + singular_suffix
        return word
    
    keywork_list1 = [singularize_word(x) for x in keywork_list]

    return keywork_list1
    

def search_OpenSearch(keywords):
    
    host = 'https://search-cchw2photosopensearch-sy3nt7l7m7an5goaumpbfl6pqe.us-east-1.es.amazonaws.com' # The OpenSearch domain endpoint with https://
    index = "photos"
    url = host + '/' + index + '/_search'
    
    # Put the user query into the query DSL for more accurate search results.
    # Note that certain fields are boosted (^).
    query = {}
    if len(keywords) == 1:
        keywords[0] = keywords[0].lower()
        query = {
            "size": 100,
            "query": {
                "term": {
                    "labels": keywords[0],
                }
            }
        }
    else:
        query = {
          "query": {
            "bool" : {
              "must": [
                { "term": { "labels": keywords[0] }},
                { "term": { "labels": keywords[1] }},
              ]
            }
          }
        }


    # Elasticsearch 6.x requires an explicit Content-Type header
    headers = { "Content-Type": "application/json" }

    # Make the signed HTTP request
    r = requests.get(url, auth=('master', 'Wjw,513203628'), headers=headers, data=json.dumps(query))

    # Create the response and add some extra content to support CORS
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": '*'
        },
        "isBase64Encoded": False
    }

    # Add the search results to the response
    lst = []
    print(r.text)
    hits = json.loads(r.text)["hits"]["hits"]
    for hit in hits:
        dic = hit["_source"]["url"]
        lst.append(dic)
    return lst
    

def lambda_handler(event, context):
    # TODO implement
    print("event", event)
    print("context", context)
    # message = "I would like to see Motorcycle and pen"
    message = event["queryStringParameters"]["q"]
    print("message: ", message)
    keywork_list = lex2_disambiguate(message)
    
    print("keywords: ", str(keywork_list))
    
    if keywork_list:
        lst = search_OpenSearch(keywork_list)
        # lst = search_OpenSearch(["rek1","cus11","no"])

        resp = {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": '*'
            },
            "isBase64Encoded": False,
            "body": json.dumps(lst)
        }
    else:
        resp = {
            'statusCode': 200,
            # 'body': "json.dumps({"results": []})"
            'body': json.dumps([])
        }
    
    
    return resp
