# Near Real-time Data Processing with Amazon Kinesis Data Streams and AWS Comprehend
Stream text data into Amazon Kinesis Data Streams, process with Amazon Comprehend and store the data in S3 with partitions.

## Installations and Requirements
1. AWS CLI - To interact with Amazon Web Services
    - Region: ```us-east-1```
    - Store ```AWS_ACCESS_KEY_ID``` and ```AWS_SECRET_ACESS_KEY``` in system enviroment variables
2. Python 3.10
    - Packages: Boto3, Pandas
3. Jupyter Notebook (Anaconda)

## Deploying Resources
### 1. Deploying Kinesis Stream and S3 buckets (CloudFormation Stack)
- The resources are defined in ```cloud_formation.yml```
- Deploy stack (run in terminal):
    - ```aws cloudformation create-stack --stack-name NewsStreamStack --template-body file://cloud_formation.yaml --capabilities CAPABILITY_NAMED_IAM```

### 2. Deploying Lambda Function (manually)
This is done manually to avoid using operations like zipping the code, pushing, replying on serverless framework etc. This is just one file, so not a lot of manual work is needed.
- Create new Lambda function on AWS Console.
    - Name: ingestion_lambda
    - Runtime: Python 3.11
    - Change default execution role: Choose ```NewsStreamLambdaExecutionRole```
- Copy and Paste the code from ```./lambdas/receive_stream.py``` to the Lambda function. Deploy the new code.
- Add trigger.
    - Select Kinesis as the trigger and choose ```news-stream``` stream.
    - Batch size = 10
    - Retry attempts = 1 (possible data loss)
    - Concurrent batches per shard = 10
- In General Configuration, change timeout to 30 seconds.
    - Very crucial

## Put data into Kinesis Data Stream
Use the jupyter notebook ```main.ipynb``` (self explanatory)

## Sample Results
Raw Text: 
```bazaar
RIYADH (Reuters) - Saudi Arabia s King Salman left on Wednesday for an official trip to Russia where he is set to meet President Vladimir Putin for talks on oil production and regional policy, state television said. Several investment deals, including on a liquefied natural gas project and petrochemical plants, could also be signed during the trip and plans for a $1-billion fund to invest in energy projects are likely to be finalised. The king appointed his son, 32-year-old Crown Prince Mohammed bin Salman, to manage the kingdom s affairs in his absence.,
```

PII Redacted Text:
```bazaar
****** (Reuters) - ************ s King ****** left on Wednesday for an official trip to ****** where he is set to meet President ************** for talks on oil production and regional policy, state television said. Several investment deals, including on a liquefied natural gas project and petrochemical plants, could also be signed during the trip and plans for a $1-billion fund to invest in energy projects are likely to be finalised. The king appointed his son, *********** Crown Prince *******************, to manage the kingdom s affairs in his absence.
```
Sentiment:
```bazaar
{
    "sentiment": {
        "Positive": 0.006651362404227257, 
        "Negative": 0.004785413388162851, 
        "Neutral": 0.9885482788085938, 
        "Mixed": 1.4994479897723068e-05
    }
}
```
## Destroying Resources
1. Delete the Lambda Function.
2. Empty the buckets and delete the stack by running the commands in ```destroy.sh``` shell script from the terminal.