#!/usr/bin/env python
"""
Create the Keys for ETH 2
"""

import sys
import argparse
import string
import subprocess
import os
import secrets
import boto3
import uuid

from eth2deposit.credentials import (
    CredentialList,
)
from eth2deposit.deposit import generate_mnemonic
from eth2deposit.utils.validation import verify_deposit_data_json
from eth2deposit.utils.constants import (
    WORD_LISTS_PATH,
    MAX_DEPOSIT_AMOUNT
)
from eth2deposit.key_handling.key_derivation.mnemonic import (
    get_languages,
    get_mnemonic,
)

from eth2deposit.settings import (
    ALL_CHAINS,
    MAINNET,
    get_setting,
)

S3_BUCKET = 'eth2-staking-keys'
DDB_METADATA_TABLE = 'Eth2-StakeData'


def main(args):
    token_id = args.id if not args.id == 'blank' else str(uuid.uuid4())
    data = {}
    data['token_id'] = token_id
    print(f'Generating Key: {token_id}')
    mnemonic_language = 'english'
    data['mnemonic'] = get_mnemonic(language=mnemonic_language, words_path=WORD_LISTS_PATH)
    print('data', data)
    folder = f'/data'
    folder = os.path.join(folder, 'validator_keys')
    setting = get_setting('medalla')
    if not os.path.exists(folder):
        os.mkdir(folder)
    credentials = CredentialList.from_mnemonic(
        mnemonic=data['mnemonic'],
        num_keys=1,
        amounts=[MAX_DEPOSIT_AMOUNT],
        fork_version=setting.GENESIS_FORK_VERSION
    )
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(20))
    data['password'] = password
    keystore_filefolders = credentials.export_keystores(password=password, folder=folder)
    deposits_file = credentials.export_deposit_data_json(folder=folder)
    assert credentials.verify_keystores(keystore_filefolders=keystore_filefolders, password=password)
    assert verify_deposit_data_json(deposits_file)
    print(f'Completed Key Generation: {token_id}')
    data = upload_keys(data)
    save_metadata(data)


def upload_keys(data):
    token_id = data['token_id']
    s3 = boto3.client('s3')
    base = '/data/validator_keys/'
    onlyfiles = [f for f in os.listdir(base) if os.path.isfile(os.path.join(base, f))]
    for filename in onlyfiles:
        print(f'Uploading {filename}')
        if filename.startswith('deposit_data'):
            s3.upload_file(f'{base}{filename}', S3_BUCKET, f'{token_id}/deposit-data.json')
            data['deposit_data'] = f's3://{S3_BUCKET}/{token_id}/deposit-data.json'
        elif filename.startswith('keystore'):
            s3.upload_file(f'{base}{filename}', S3_BUCKET, f'{token_id}/keystore.json')
            data['keystore'] = f's3://{S3_BUCKET}/{token_id}/keystore.json'
        else:
            s3.upload_file(f'{base}{filename}', S3_BUCKET, f'{token_id}/{filename}')
    return data


def save_metadata(data):
    ddb = boto3.client('dynamodb')
    ddb.put_item(
        TableName=DDB_METADATA_TABLE,
        Item={
            "token_id": {'S': data['token_id']},
            "password": {'S': data['password']},
            "mnemonic": {'S': data['mnemonic']},
            "deposit-data": {'S': data['deposit_data']},
            "keystore": {'S': data['keystore']},
        }
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=str, required=False, default='blank', help='ID of the keys')
    args = parser.parse_args()
    main(args)
