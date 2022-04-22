import json
import logging
from logging.handlers import RotatingFileHandler
import random

import boto3
from botocore.exceptions import ClientError
from decouple import config

# ENVIRONMENT VARIABLES

# AWS
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = config("AWS_DEFAULT_REGION")

# SQS
aws_sqs_url = config("SQS_URL")
NUM_MSG_GROUP_ID = config("NUM_MSG_GROUP_ID", default=5, cast=int)  # FIFO throughput limit = Per message group ID

# Python
ENV = config("ENV", default="production")
IS_LOGGER_ENABLED = config("IS_LOGGER_ENABLED", default=True, cast=bool)


# CONFIGURE LOGS
handler = RotatingFileHandler(
    "logs/sqs_functions.log", 
    mode="w", 
    encoding="utf-8", 
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=3,
)
format = logging.Formatter(fmt='%(levelname)s - %(asctime)s - %(filename)s -  %(funcName)s() - %(message)s')
handler.setFormatter(format)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.disabled = not IS_LOGGER_ENABLED


# DEFINE CLASS AND FUNCTIONS

def send_message(qrn):
    """ Send a message to a SQS queue """

    sqs_client = boto3.client("sqs", region_name=AWS_DEFAULT_REGION)

    message = {
        "qrn": qrn
    }

    try:
        send_response = sqs_client.send_message(
            QueueUrl = aws_sqs_url,
            MessageBody = json.dumps(message),
            MessageGroupId = str(random.randrange(1,NUM_MSG_GROUP_ID))
        )
    except ClientError as error:
        logger.exception("Send message failed: %s", 'dummy')
        raise error
    else:
        logger.info("SQS send_message() response = %s", str(send_response))
        return send_response


def receive_message(num_recv_msgs):
    """ Receive a message(s) from a SQS queue 
    
    : param num_recv_msgs: Number of SQS messages to receive in a single call 
    """

    sqs_client = boto3.client("sqs", region_name=AWS_DEFAULT_REGION)
    
    try:
        receive_response = sqs_client.receive_message(
            QueueUrl = aws_sqs_url,
            MaxNumberOfMessages = num_recv_msgs, 
            WaitTimeSeconds = 10,   # The time (in seconds) which a ReceiveMessage call blocks oﬀ on the server, waiting for messages to appear in the queue before returning with an empty receive result.
        )
    except ClientError as error:
        logger.exception("Receive message failed: %s", 'dummy')
        raise error
    else:
        logger.info("Number of messages received: %s", len(receive_response.get('Messages', [])))
        logger.info( "SQS receive_message() response = %s", str(receive_response) )
        if(ENV != "production"): print( "Number of messages received = %s", len(receive_response.get('Messages', [])) )
        return receive_response


def delete_message(receipt_handle):
    """ Delete the message from a SQS queue """

    sqs_client = boto3.client("sqs", region_name=AWS_DEFAULT_REGION)

    try:
        delete_response = sqs_client.delete_message(
            QueueUrl = aws_sqs_url,
            ReceiptHandle = receipt_handle,
        )
    except ClientError as error:
        logger.exception("Delete message failed: %s", str(delete_response))
        raise error
    else:
        logger.info("SQS delete_message() response = %s", str(delete_response))
        return delete_response


def purge_queue():
    """ Delete all the messages from a SQS queue """

    sqs_client = boto3.client("sqs", region_name=AWS_DEFAULT_REGION)

    try:
        purge_response = sqs_client.purge_queue(
            QueueUrl = aws_sqs_url,
        )
    except ClientError as error:
        logger.exception("Purge message failed: %s", str(purge_response))
        raise error
    else:
        logger.info("SQS purge_message() response = %s", str(purge_response))
        return purge_response
