"""
The code is developed using reference from
https://docs.aws.amazon.com/textract/latest/dg/examples-blocks.html
"""
import random
import requests
import json
import logging
import boto3
from botocore.config import Config

# Python trp module is Amazon textract result parser
# https://pypi.org/project/textract-trp/
# You have uploaded module using Lambda Layer.
from trp import Document
from urllib.parse import unquote_plus

# It is good practice to use proper logging.
# Here we are using the logging module of python.
# https://docs.python.org/3/library/logging.html

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Boto3 - s3 Client
# More Info: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rekognition.html



my_config = Config(
    region_name = 'ap-southeast-2',
)
s3 = boto3.client('s3',config=my_config)

# Declare output file path and name
output_key = "output/textract_response.json"


confluence_base_url = 'https://unihack-lecture.atlassian.net/wiki'
apiToken = 'ATATT3xFfGF0sVeg6ZJQhIpvmllwTYzixrKqv4W7rPEPRUR2mRqsNSBDjbyMWsLuqw-R53kuKqCo_eBFcFmcqFxSh9m0RwvmKgbZWEQhBefUk1wxM3vBOD08T6NklRAhka5tf_kyu3u5mDIoTtEbZvEvT9B4ZPvDS-ylJDUVtq8a3pJ4MNfO8qw=9024E2C2'
email = 'hyzhou@student.unimelb.edu.au'

auth = (email, apiToken)
headers = {
    'Content-Type': 'application/json'
}

def lambda_handler(event, context):
    """
    This code gets the S3 attributes from the trigger event,
    then invokes the textract api to analyze documents synchronously.
    """
    def uploadTranscript(title, new_content):
        data = {
            'type': 'page',
            'title': title,
            'space': {'key': 'TEAM'},
            'body': {
                'storage': {
                    'value': new_content,
                    'representation': 'storage',
                }
            }
        }
        
        create_url = f'{confluence_base_url}/rest/api/content/'
        response = requests.post(create_url, data=json.dumps(data), headers=headers, auth=auth)
    
        if response.status_code == 200:
            print("Page created successfully.")
            # Print the URL of the newly created page
            page_id = response.json()['id']
            print(f"Page URL: {confluence_base_url}/spaces/TEAM/pages/{page_id}")
        else:
            print("Failed to create page:", response.json())





    # log the event
    logger.info(event)
    # Iterate through the event
    for record in event['Records']:
        # Get the bucket name and key for the new file
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        # Using Amazon Textract client
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract.html
        textract = boto3.client('textract',config=my_config)

        # Analyze document
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract.html#Textract.Client.analyze_document
        try:
            response = textract.analyze_document(   # You are calling analyze_document API
                Document={                          # to analyzing document Stored in an Amazon S3 Bucket
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                FeatureTypes=['FORMS','TABLES',  # FeatureTypes is a list of the types of analysis to perform.
                              ])                            # Add TABLES to the list to return information about
                                                            # the tables that are detected in the input document.
                                                            # Add FORMS to return detected form data. To perform both
                                                            # types of analysis, add TABLES and FORMS to FeatureTypes .

            doc = Document(response)  # You are parsing the textract response using Document.

            # The below code reads the Amazon Textract response and
            # prints the Key and Value
            text = []
            for page in doc.pages:
                # Print fields
                print("Fields:")
                for field in page.form.fields:
                    print(field)
                    text.append(str(field.key))
                    text.append(str(field.value))
            text = ''.join(text)
            print(text)
            name = "slides"
            random_number = random.randint(1, 1000)
            name = name+str(random_number)
            
            uploadTranscript(name, text)

                    # Search fields by key
                    # Enter your code below

            # The below code reads the Amazon Textract response and
            # prints the Table data. Uncomment below to use the code.

            for page in doc.pages:
                print("\nTable details:")
                for table in page.tables:
                    for r, row in enumerate(table.rows):
                        for c, cell in enumerate(row.cells):
                            print("Table[{}][{}] = {}".format(r, c, cell.text))

            return_result = {"Status": "Success"}

            # Finally the response file will be written in the S3 bucket output folder.
            s3.put_object(
                Bucket=bucket,
                Key=output_key,
                Body=json.dumps(response, indent=4)
            )

            return return_result
        except Exception as error:
            return {"Status": "Failed", "Reason": json.dumps(error, default=str)}


"""
You can use below code to create test event to test
the Lambda function.
{
    "Records": [
                {
                "s3": {
                    "bucket": {
                    "name": "<Your_bucket_name>"
                    },
                    "object": {
                    "key": "input/employment_form.png"
                    }
                }
                }
            ]
}
"""
