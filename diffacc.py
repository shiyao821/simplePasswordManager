import json
from pwmdata import Account, decode_datetime, DateTimeEncoder, decrypt_file_data

FILE_NAME_A = 'accounts.data'
FILE_NAME_B = 'accountsfromphone.data'


def load(filename, password) -> dict[str, Account]:
    with open(filename, 'rb') as f:
        raw = f.read()
    decrypted, _ = decrypt_file_data(raw, password)
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

    print(f'{len(exclusive_a)} accounts exclusive to file {FILE_NAME_A}')
    for acc in exclusive_a:
        print(acc_json(acc))
    print()

    print(f'{len(exclusive_b)} accounts exclusive to file {FILE_NAME_B}')
    for acc in exclusive_b:
        print(acc_json(acc))
    print()

    print(f'{len(newer_in_a)} accounts newer in {FILE_NAME_A}')
    for acc_a, acc_b in newer_in_a:
        print('\t' + acc_json(acc_a))
        print('\t' + acc_json(acc_b))
    print()

    print(f'{len(newer_in_b)} accounts newer in {FILE_NAME_B}')
    for acc_a, acc_b in newer_in_b:
        print('\t' + acc_json(acc_a))
        print('\t' + acc_json(acc_b))
    print()


if __name__ == '__main__':
    a = load(FILE_NAME_A, input("Password for File A: "))
    b = load(FILE_NAME_B, input("Password for File B: "))
    compare(a, b)
