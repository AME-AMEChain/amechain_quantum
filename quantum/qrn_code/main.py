"""
Purpose

The main program that gets QRN from Quantum source, and
writes to the entropy pool.
"""

import json
import logging
import multiprocessing
import os
import time
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
from threading import current_thread

import schedule
from decouple import config

import qrn_api
import sqs_functions

# ENVIRONMENT VARIABLES

# QRN
RAND_TYPE = config("RAND_TYPE", default="hex")
QRN_LENGTH = config("QRN_LENGTH", default=100, cast=int)

# SQS
SQS_ACTION = config("SQS_ACTION", default="SEND")       # "SEND" or "RECEIVE". Take from .env file
NUM_RECV_MSGS = config("NUM_RECV_MSGS", default=5, cast=int)    # Number of SQS messages to receive per call

# Multithreading
N_PROCESSES = multiprocessing.cpu_count()
SENDMSG_MAX_WORKERS = config("SENDMSG_MAX_WORKERS", default=4, cast=int)
SENDMSG_N_THREADS = config("SENDMSG_N_THREADS", default=4, cast=int)
RECVMSG_MAX_WORKERS = config("RECVMSG_MAX_WORKERS", default=4, cast=int)
RECVMSG_N_THREADS = config("RECVMSG_N_THREADS", default=4, cast=int)

# Python
ENV = config("ENV", default="production")
IS_LOGGER_ENABLED = config("IS_LOGGER_ENABLED", default=True, cast=bool)

if(SQS_ACTION == "SEND"):
    MAX_WORKERS = SENDMSG_MAX_WORKERS   # maximum number of workers acting on {all threads put together}
    N_THREADS = SENDMSG_N_THREADS       # the number of actual threads
elif(SQS_ACTION == "RECEIVE"):
    MAX_WORKERS = RECVMSG_MAX_WORKERS
    N_THREADS = RECVMSG_N_THREADS

if(ENV != "production"): print(f"SQS ACTION = {SQS_ACTION}") 


# CONFIGURE LOGS
handler = RotatingFileHandler(
    "logs/main.log",
    mode = "w",
    encoding = "utf-8",
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

# dev_random = os.open("/dev/random", os.O_RDWR)
dev_urandom = os.open("/dev/urandom", os.O_RDWR)
if (ENV == "development"):
    txt_file = os.open("logs/check_writes.log", os.O_RDWR)
    # verified to be writing the QRN to the file in binary format

def get_qrn():
    """ Get QRN from QRN API and return it """

    getqrn_obj = qrn_api.GetQrn(RAND_TYPE, QRN_LENGTH)
    qrn = getqrn_obj.get_qrn()
    if(ENV != "production"): print(f"QRN = {qrn}")
    logger.info("QRN is received")
    return qrn

def add_entropy(qrn_hex):
    """ write the QRN into the devices /dev/random and /dev/urandom """

    logger.info("type(qrn_hex) = %s", type(qrn_hex))
    logger.info("qrn_hex: %s", qrn_hex)

    qrn_bin = bytes.fromhex(qrn_hex)
    logger.info("type(qrn_bin) = %s", type(qrn_bin))
    logger.info("qrn_bin: %s", qrn_bin)

    qrn_bin_to_hex = bytes.hex(qrn_bin)
    logger.info("type(qrn_bin_to_hex) = %s", type(qrn_bin_to_hex))
    logger.info("qrn_bin_to_hex: %s", qrn_bin_to_hex)       # verified to be the same as qrn_hex

    # os.write(dev_random, qrn_bin)     # No need to write duplicates to entropy pool
    os.write(dev_urandom, qrn_bin)
    if (ENV == "development"):
        os.write(txt_file, qrn_bin)

    # random_read = os.read(dev_random, 16)
    # logger.info("A read from /dev/random gave: %s %s", random_read, random_read.hex())

    # urandom_read = os.read(dev_urandom, 16)
    # logger.info("A read from /dev/urandom gave: %s %s", urandom_read, urandom_read.hex())

    return True

def process_sqs_response():
    """ Receive messages from a SQS queue. 
    Process them i.e write to entropy pool
    Delete them after processing 
    """

    receive_response = sqs_functions.receive_message(NUM_RECV_MSGS)

    for message in receive_response.get("Messages", []):
        receipt_handle = message['ReceiptHandle']
        message_body = message["Body"]
        qrn = json.loads(message_body)["qrn"]
        logger.info("Receipt Handle: %s", receipt_handle)
        logger.info("Message body: %s", message_body)
        logger.info("QRN: %s", qrn)

        add_entropy(qrn)
        delete_response = sqs_functions.delete_message(receipt_handle)

    return True

def unit_task():
    """
    Define the unit task for concurrent.futures to work on.
    1) Get QRN, Send message to SQS 0r 2) Receive and delete messages.
    """

    thread_id = current_thread().ident
    logger.info("Thread ID = %s", thread_id)     # %s formatting in logger saves you from evaluating strings that might not be used at all

    if(SQS_ACTION == "SEND"):
        qrn = get_qrn()
        sqs_functions.send_message(qrn)

    elif(SQS_ACTION == "RECEIVE"):
        receipt_handles = process_sqs_response()
        return receipt_handles

def concurrent_tasks():
    """ Takes unit_task, runs multiple copies of it in parallel """

    ts = time.time()

    # with ProcessPoolExecutor() as executor:
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i in range(N_THREADS):
            logger.info("Iteration %s", i)
            future = executor.submit(unit_task)

    logger.info('Took %s seconds', time.time() - ts)
    logger.info("Number of concurrent threads/processes = %s", MAX_WORKERS)
    logger.info("Number of Iterations of concurrent_tasks() = %s", N_THREADS)

def run_scheduler():
    """ Schedule a job at regular intervals """

    schedule.every(10).seconds.do(concurrent_tasks)

    while True:
        schedule.run_pending()
        time.sleep(1)


# START THE PROGRAM

if __name__ == '__main__':
    run_scheduler()
    
