import json
from cryptography.fernet import Fernet
from pwmdata import Account, decode_datetime, DateTimeEncoder, derive_key

FILE_NAME_A = 'accounts.data'
FILE_NAME_B = 'accountsfromphone.data'
OUTPUT_FILE_NAME = 'compare.result'


def load(filename, password) -> dict[str, Account]:
    with open(filename, 'rb') as f:
        encrypted = f.read()
    decrypted = Fernet(derive_key(password)).decrypt(encrypted)
    accounts = {}
    for line in decrypted.splitlines():
        acc = Account(**json.loads(line.decode('utf-8'), object_hook=decode_datetime))
        accounts[acc.accountName] = acc
    return accounts


def compare(a: dict[str, Account], b: dict[str, Account]):
    exclusive_a = [v for k, v in a.items() if k not in b]
    exclusive_b = [v for k, v in b.items() if k not in a]
    newer_in_a  = [[a[k], b[k]] for k in a if k in b and a[k].lastEdited > b[k].lastEdited]
    newer_in_b  = [[a[k], b[k]] for k in a if k in b and b[k].lastEdited > a[k].lastEdited]

    def acc_json(acc):
        return json.dumps(acc.__dict__, cls=DateTimeEncoder)

    output = ''
    output += f'{len(exclusive_a)} accounts exclusive to file {FILE_NAME_A}\n'
    for acc in exclusive_a:
        output += acc_json(acc) + '\n'
    output += '\n'

    output += f'{len(exclusive_b)} accounts exclusive to file {FILE_NAME_B}\n'
    for acc in exclusive_b:
        output += acc_json(acc) + '\n'
    output += '\n'

    output += f'{len(newer_in_a)} accounts newer in {FILE_NAME_A}\n'
    for acc_a, acc_b in newer_in_a:
        output += '\t' + acc_json(acc_a) + '\n'
        output += '\t' + acc_json(acc_b) + '\n'
    output += '\n'

    output += f'{len(newer_in_b)} accounts newer in {FILE_NAME_B}\n'
    for acc_a, acc_b in newer_in_b:
        output += '\t' + acc_json(acc_a) + '\n'
        output += '\t' + acc_json(acc_b) + '\n'
    output += '\n'

    with open(OUTPUT_FILE_NAME, 'wb') as f:
        f.write(output.encode('utf-8'))


if __name__ == '__main__':
    a = load(FILE_NAME_A, input("Password for File A: "))
    b = load(FILE_NAME_B, input("Password for File B: "))
    compare(a, b)
