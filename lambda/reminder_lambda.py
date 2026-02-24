import json
import boto3
import uuid
import os

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE = os.environ['TABLE_NAME']
TOPIC = os.environ['TOPIC_ARN']
DEADLINE = os.environ['ENROLLMENT_DEADLINE']


def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    action_group = event.get("actionGroup", "")
    function_name = event.get("function", "")
    api_path = event.get("apiPath", "")
    http_method = event.get("httpMethod", "")

    # Extract Bedrock parameters 
    frequency = "24" #default

    parameters = event.get("parameters", [])

    for param in parameters:
        if param.get("name") == "frequency_hours":
            frequency = param.get("value")

    reminder_id = str(uuid.uuid4())

    table = dynamodb.Table(TABLE)

    # dynamoDB entries for storing user choice
    table.put_item(Item={
        "reminderId": reminder_id,
        "frequencyHours": frequency
    })

    # email body
    message = f"Reminder: Please enroll into your subjects before {DEADLINE}"

    # email subject for the subscribed email
    sns.publish(
        TopicArn=TOPIC,
        Message=message,
        Subject="University Enrollment Reminder"
    )

    # returning the response format suitable for bedrock
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "function": function_name,
            "apiPath": api_path,
            "httpMethod": http_method, 
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": f"Reminder created successfully. Emails will be sent every {frequency} hours."
                    }
                }
            }
        }
    }