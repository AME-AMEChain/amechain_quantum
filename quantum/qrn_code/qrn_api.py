import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler

import requests
from decouple import config

# ENVIRONMENT VARIABLES

# QRN API
BASEURL = config('QRN_URL')
API_KEY  = config('QRN_API_KEY')
SALT = config('QRN_API_SALT')

# Python
IS_LOGGER_ENABLED = config("IS_LOGGER_ENABLED", default=True, cast=bool)

# CONFIGURE LOGS
handler = RotatingFileHandler(
    "logs/qrn_api.log", 
    mode="w", 
    encoding="utf-8",
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=3,
)
format = logging.Formatter(
    fmt='%(levelname)s - %(asctime)s - %(filename)s -  %(funcName)s() - %(message)s'
)
handler.setFormatter(format)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.disabled = not IS_LOGGER_ENABLED


# DEFINE CLASS AND FUNCTIONS

class GetQrn:
    """ A class that contains methods and attributes to get QRN from QRN API """
    
    DICT_RAND_TYPES = {
        "hex": {
            "rand_type_code": 0,
            "path": "/api/v1/randhex",
        },
        "bin": {
            "rand_type_code": 1,
            "path": "/api/v1/randbin",
        },
        "base64": {
            "rand_type_code": 2,
            "path": "/api/v1/randbase64",
        },
        "int": {
            "rand_type_code": 3,
            "path": "/api/v1/randint",
        },
        "float": {
            "rand_type_code": 4,
            "path": "/api/v1/randfloat",
        },
    }

    def __init__(self, rand_type, length):
        self.rand_type = rand_type      # rand_type = hex/bin/base64/int/float
        self.length = length

    def get_qrn(self):
        """ Use QRN API and get QRN (Quantum Random Number) """
        
        # convert salt to hash digest
        rand_type_code = __class__.DICT_RAND_TYPES[self.rand_type]["rand_type_code"]
        hash_string = str(API_KEY) + str("|") + str(rand_type_code) + str("|") + str(self.length) + str("|") + str(SALT)
        hash_digest = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()
        logger.info(f"string_to_be_hashed = {hash_string}")
        logger.info("hash digest = " + hash_digest)

        # POST parameters
        post_params = json.dumps(   # post parameters must be structured in json format
            {
                "Api_key": API_KEY,
                "Rand_type": rand_type_code,
                "Length": self.length,
                "Hash": hash_digest
            }
        )   
        full_url = BASEURL + __class__.DICT_RAND_TYPES[self.rand_type]["path"]
        logger.info("FULL_URL = " + full_url)
        logger.info("post_params = " + post_params)
        # time.sleep(2)

        # sending the POST request
        response = requests.post(
            full_url, 
            data = post_params, 
            verify = "cert_files/BUNDLE.pem",  # Verify valid/invalid SSL certificates
            headers = {
                'Content-Type': 'application/json',
            }
        )
        
        # processing the response
        response_json = response.json()
        logger.info("qrn response.content = " + str(response.content))
        logger.info("Status code = " + str(response.status_code))
        # logger.info("Response content = " + str(response_json.content))
        qrn = response_json['random']
        logger.info("QRN = " + qrn)

        return qrn

