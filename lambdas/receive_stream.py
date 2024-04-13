import json
import ast
import base64
import datetime
import uuid

import boto3

# PATHS
S3_BUCKET_RAW_DATA = "stream-raw-210570"
S3_BUCKET_REDACTED_DATA = "stream-redacted-210570"
S3_BUCKET_ANALYTICS = "stream-analytics-210570"


def upload_dict_to_s3(data: dict, bucket_name: str, ):

    s3_client = boto3.client('s3')
    timestamp = datetime.datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
    
    YEAR = timestamp.year
    MONTH = timestamp.month
    DATE = timestamp.day

    FILE_KEY = f"{YEAR}/{MONTH}/{DATE}/{data['id']}.json"
    # print(f"Uploading {FILE_KEY} to bucket {bucket_name}")
    JSON_STRING = json.dumps(data)
    
    response = s3_client.put_object(
        Bucket=bucket_name,
        Key=FILE_KEY,
        Body=JSON_STRING
    )
    
    return


def decode_records(records: list[dict]) -> list:
    decoded_records = []

    for record in records:

        data = base64.b64decode( record['kinesis']['data'] ).decode('utf-8')
        data = ast.literal_eval(data)

        data['timestamp'] = str(
            datetime.datetime.fromtimestamp( record['kinesis']['approximateArrivalTimestamp'] )
        )

        data['id'] = uuid.uuid4().hex
        decoded_records.append(data)
    return decoded_records


def get_redacted_records(records: list[dict]):

    comprehend_client = boto3.client('comprehend')
    redacted_records = []

    for data in records:
        try:
            new_record = {}
            response = comprehend_client.contains_pii_entities(Text=data['text'], LanguageCode='en')
            if response['Labels'] == []:
                continue
            else:
                response = comprehend_client.detect_pii_entities(Text=data['text'], LanguageCode='en')
                entities = response['Entities']
                redacted_text = data['text']
                for entity in entities:
                    start, end = entity['BeginOffset'], entity['EndOffset']
                    redacted_text = redacted_text[:start] + '*'*(end-start) + redacted_text[end:]
                new_record['text'] = redacted_text
                new_record['id'] = data['id']
                new_record['timestamp'] = data['timestamp']
            redacted_records.append(new_record)
        except Exception as e:
            print(f"One failure in get_redacted_records : {e}")
    
    return redacted_records


def get_sentiment_analysis(records: list[dict]):
    comprehend_client = boto3.client('comprehend')
    sentiment_records = []

    for data in records:
        try:
            new_record = {}
            new_record['sentiment'] = comprehend_client.detect_sentiment(
                Text=data['text'], LanguageCode='en'
            )['SentimentScore']
    
            new_record['id'] = data['id']
            new_record['timestamp'] = data['timestamp']
            sentiment_records.append(new_record)
        except Exception as e:
            print(f"One failure in get_sentiment_analysis : {e}")
    
    return sentiment_records


def lambda_handler(event, context):
    kinesis_client = boto3.client('kinesis')

    raw_records = decode_records(event['Records'])
    print(f"Decoded {len(raw_records)} records successfully")
    sentiment_records = get_sentiment_analysis(raw_records)
    print(f"Sentiment extracted for {len(sentiment_records)} records")
    redacted_records = get_redacted_records(raw_records)
    print(f"Redaction complete for {len(redacted_records)} records")

    [upload_dict_to_s3(data=current_data, bucket_name=S3_BUCKET_RAW_DATA) for current_data in raw_records]
    [upload_dict_to_s3(data=current_data, bucket_name=S3_BUCKET_ANALYTICS) for current_data in sentiment_records]
    [upload_dict_to_s3(data=current_data, bucket_name=S3_BUCKET_REDACTED_DATA) for current_data in redacted_records]
    print("Upload to S3 complete")
    return {
        'statusCode': 200,
        'body': json.dumps('Records processed successfully!')
    }
