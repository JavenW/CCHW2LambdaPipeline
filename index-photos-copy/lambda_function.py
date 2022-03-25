import json
import boto3
import urllib.parse
import datetime
import requests

def detect_rekog_labels(photo, bucket):

    client=boto3.client('rekognition')

    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=10, MinConfidence=60)

    print('Detected labels for ' + photo) 
    labels = []
    for label in response['Labels']:
        labels.append(label['Name'])
    return labels

def retrive_custom_labels(photo, bucket):

    client = boto3.client('s3')
    headObjects = client.head_object(
        Bucket=bucket,
        Key=photo,
    )
    print(headObjects)
    time = headObjects["LastModified"].isoformat()
    if "customlabels" not in headObjects["Metadata"]:
        return time, []
    customLabels = str(headObjects["Metadata"]["customlabels"]).split(",")
    
    return time, customLabels
    

def store_opensearch(picName, json_data):
    
    headers = {
        # Already added when you pass json= but not when you pass data=
        # 'Content-Type': 'application/json',
    }
    
    response = requests.put("https://search-cchw2photosopensearch-sy3nt7l7m7an5goaumpbfl6pqe.us-east-1.es.amazonaws.com/photos/_doc/"+str(picName), headers=headers, json=json_data, auth=('master', 'Wjw,513203628'))
    
    print(response)
    
    

def lambda_handler(event, context):
    # TODO implement
    
    print(event)
    
    s3 = event["Records"][0]["s3"]
    bucket = s3["bucket"]["name"]
    urlName = s3["object"]["key"]
    picName = urllib.parse.unquote_plus(urlName)
    print("picName ", picName)
    
    rekogLabels=detect_rekog_labels(picName, bucket)
    rekogLabels = [x.lower() for x in rekogLabels]
    print("Labels detected: " + str(rekogLabels))
    
    # rekogLabels = ["rek1", "rek2"]
    
    time, customLabels = retrive_custom_labels(picName, bucket)
    
    # time = "2011-11-04T00:05:23"
    # customLabels = ["cus1","cus2"]
    
    
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
    
    customLabels = [singularize_word(x).lower() for x in customLabels]
    
    print("customLabels: ", customLabels)
    
    totalLabels  = list(set(rekogLabels + customLabels))
    
    print("totalLabels: ", totalLabels)
    
    ret_dict = {
        "objectKey": picName,
        "bucket": bucket,
        "createdTimestamp": time,
        "labels": totalLabels,
        "url": "https://cchw2photostorage.s3.amazonaws.com/"+urlName
    }
    
    print("dict: ", str(ret_dict))
    
    store_opensearch(picName, ret_dict)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successful actions from Lambda index-photos!')
    }
