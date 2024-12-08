import json
from json import JSONEncoder
from base64 import urlsafe_b64encode
from copy import copy
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime as dt
from pwmdata import Account, DecodeDateTime, DateTimeEncoder
import datetime

FILE_NAME_A = 'accounts.data'
FILE_NAME_B = 'accountsfromphone.data'
OUTPUT_FILE_NAME = 'compare.result'

# return dic of Accounts
def load(filename, password):
  with open(filename, 'rb') as inputFile:
    accounts = {}
    encrypted = inputFile.read()
    # decrypt file based on self.masterPassword
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'69420', iterations=69420)
    key = urlsafe_b64encode(kdf.derive(bytes(password, 'utf-8')))
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted)

    for line in decrypted.splitlines():
      acc = Account(**json.loads(str(line, 'utf-8'), object_hook=DecodeDateTime))
      accounts[acc.accountName] = acc
    return accounts

def compare(a, b):
  exclusiveA = [] # accounts in A but not in B
  exclusiveB = [] # accounts in B but not in A
  newerInA = []
  newerInB = []
  for k, v in a.items():
    if k not in b:
      exclusiveA.append(v)
    elif b[k].lastEdited > v.lastEdited:
      newerInB.append([v, b[k]])
    elif b[k].lastEdited < v.lastEdited:
      newerInA.append([v, b[k]])
  for k, v in b.items():
    if k not in a:
      exclusiveB.append(v)
  
  with open(OUTPUT_FILE_NAME, 'wb') as outputFile:
    json_string = ''
    json_string += f'{len(exclusiveA)} accounts exclusive to file {FILE_NAME_A}\n'
    for acc in exclusiveA:
      json_string += json.dumps(acc.__dict__, cls=DateTimeEncoder) + '\n'
    
    json_string += '\n'

    json_string += f'{len(exclusiveB)} accounts exclusive to file {FILE_NAME_B}\n'
    for acc in exclusiveB:
      json_string += json.dumps(acc.__dict__, cls=DateTimeEncoder) + '\n'

    json_string += '\n'

    json_string += f'{len(newerInA)} accounts newer in {FILE_NAME_A}\n'
    for pair in newerInA:
      accA, accB = pair[0], pair[1]
      json_string += '\t' + json.dumps(accA.__dict__, cls=DateTimeEncoder) + '\n'
      json_string += '\t' + json.dumps(accB.__dict__, cls=DateTimeEncoder) + '\n'

    json_string += '\n'

    json_string += f'{len(newerInB)} accounts newer in {FILE_NAME_B}\n'
    for pair in newerInB:
      accA, accB = pair[0], pair[1]
      json_string += '\t' + json.dumps(accA.__dict__, cls=DateTimeEncoder) + '\n'
      json_string += '\t' + json.dumps(accB.__dict__, cls=DateTimeEncoder) + '\n'

    json_string += '\n'

    outputFile.write(json_string.encode('utf-8'))


if __name__ == '__main__':
  a = load(FILE_NAME_A, input("Password for File A:"))
  b = load(FILE_NAME_B, input("Password for File B:"))
  compare(a, b)
