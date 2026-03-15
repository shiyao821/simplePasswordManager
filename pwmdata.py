import json
from json import JSONEncoder
from base64 import urlsafe_b64encode
from copy import copy
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime as dt
import datetime

### Data module for pwm.py
# Abstracts data operations away from UX concerns.

_KDF_SALT = b'69420'
_KDF_ITERATIONS = 69420


def derive_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_KDF_SALT, iterations=_KDF_ITERATIONS)
    return urlsafe_b64encode(kdf.derive(password.encode('utf-8')))


class Account:
    def __init__(self, accountName='', username='', email='', password='', phone='',
                 linkedAccounts=None, misc=None, lastEdited=None):
        self.accountName = accountName
        self.username = username
        self.email = email
        self.password = password
        self.phone = phone
        self.linkedAccounts = linkedAccounts if linkedAccounts is not None else []
        self.misc = misc if misc is not None else {}
        self.lastEdited = lastEdited if lastEdited is not None else dt.now()


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()


def decode_datetime(d: dict) -> dict:
    if 'lastEdited' in d:
        d['lastEdited'] = dt.fromisoformat(d['lastEdited'])
    return d


class EmptyInputException(Exception):
    pass


class Database:
    DATA_FILE_NAME = 'accounts.data'

    def __init__(self):
        self.masterPassword = ''
        self.accountList: list[Account] = []
        self.usernameList: list[str] = []
        self.emailList: list[str] = []
        self.passwordList: list[str] = []
        self.phoneList: list[str] = []
        self.linkedAccountsList: list[str] = []

    def load(self, password: str):
        with open(self.DATA_FILE_NAME, 'rb') as f:
            encrypted = f.read()
        self.masterPassword = password
        decrypted = Fernet(derive_key(password)).decrypt(encrypted)
        for line in decrypted.splitlines():
            acc = Account(**json.loads(line.decode('utf-8'), object_hook=decode_datetime))
            self.accountList.append(acc)
        self.updateLists()
        return self

    def save(self):
        self.sortAlphaNumeric()
        self.updateLists()
        json_lines = '\n'.join(json.dumps(acc.__dict__, cls=DateTimeEncoder) for acc in self.accountList) + '\n'
        encrypted = Fernet(derive_key(self.masterPassword)).encrypt(json_lines.encode('ascii'))
        with open(self.DATA_FILE_NAME, 'wb') as f:
            f.write(encrypted)

    def numAccounts(self) -> int:
        return len(self.accountList)

    def sortAlphaNumeric(self, reverse=False):
        self.accountList.sort(key=lambda a: a.accountName, reverse=reverse)

    def filterAccountsByAccountName(self, keyword: str) -> list[Account]:
        if len(keyword) == 1:
            return [a for a in self.accountList if a.accountName.startswith(keyword)]
        return [a for a in self.accountList if keyword in a.accountName]

    def filterAccountsByEmail(self, email: str) -> list[Account]:
        return [a for a in self.accountList if a.email == email]

    def filterAccountsByUsername(self, username: str) -> list[Account]:
        return [a for a in self.accountList if a.username == username]

    def filterAccountsByPassword(self, password: str) -> list[Account]:
        return [a for a in self.accountList if a.password == password]

    def filterAccountsByPhone(self, phone: str) -> list[Account]:
        return [a for a in self.accountList if a.phone == phone]

    def filterAccountsByLinkedAccounts(self, accountName: str) -> list[Account]:
        return [a for a in self.accountList if accountName in a.linkedAccounts]

    def addAccount(self, account: Account) -> Account:
        if account.accountName:
            self.accountList.append(account)
            self.save()
        return account

    def deleteAccount(self, account: Account):
        accountName = copy(account.accountName)
        for acc in self.accountList:
            if acc == account:
                self.accountList.remove(acc)
                del acc
                print(f'Account for {accountName} deleted')
                break
        self.save()

    def checkAccountNameExists(self, name: str) -> bool:
        return name in [acc.accountName for acc in self.accountList]

    def editAccountName(self, account: Account, text: str) -> Account:
        if not text:
            print('Cannot enter empty account name')
            return account
        if self.checkAccountNameExists(text):
            print(f'Account name "{text}" already exists')
            return account
        oldName = account.accountName
        account.accountName = text
        account.lastEdited = dt.now()
        self.updateAllLinkedAccountInstances(oldName, text)
        self.save()
        return account

    def updateAllLinkedAccountInstances(self, oldName: str, newName: str):
        for acc in self.accountList:
            if oldName in acc.linkedAccounts:
                acc.linkedAccounts = [newName if la == oldName else la for la in acc.linkedAccounts]
                acc.lastEdited = dt.now()

    def editUsername(self, account: Account, text: str) -> Account:
        account.username = text
        account.lastEdited = dt.now()
        self.save()
        return account

    def editEmail(self, account: Account, text: str) -> Account:
        account.email = text
        account.lastEdited = dt.now()
        self.save()
        return account

    def editPassword(self, account: Account, text: str) -> Account:
        account.password = text
        account.lastEdited = dt.now()
        self.save()
        return account

    def editPhone(self, account: Account, text: str) -> Account:
        if not text:
            raise EmptyInputException
        if not self.isPhoneNumber(text):
            print(f'"{text}" is not a valid phone number (digits and leading "+" only)')
            return account
        account.phone = text
        account.lastEdited = dt.now()
        self.save()
        return account

    def editLinkedAccounts(self, account: Account, text: str) -> Account:
        if text in account.linkedAccounts:
            account.linkedAccounts.remove(text)
        else:
            if text not in [acc.accountName for acc in self.accountList]:
                print(f'Account "{text}" does not exist. Create it first.')
                return account
            account.linkedAccounts.append(text)
            account.lastEdited = dt.now()
        self.save()
        return account

    def editMiscField(self, account: Account, field: str, value: str) -> Account:
        if value == '':
            del account.misc[field]
        else:
            account.misc[field] = value
        account.lastEdited = dt.now()
        self.save()
        return account

    def isPhoneNumber(self, text: str) -> bool:
        if not text:
            return False
        stripped = text[1:] if text[0] == '+' else text
        return stripped.isnumeric()

    def updateLists(self):
        self.usernameList = []
        self.emailList = []
        self.passwordList = []
        self.phoneList = []
        self.linkedAccountsList = []
        for acc in self.accountList:
            if acc.username not in self.usernameList:
                self.usernameList.append(acc.username)
            if acc.email not in self.emailList:
                self.emailList.append(acc.email)
            if acc.password not in self.passwordList:
                self.passwordList.append(acc.password)
            if acc.phone not in self.phoneList:
                self.phoneList.append(acc.phone)
            for la in acc.linkedAccounts:
                if la not in self.linkedAccountsList:
                    self.linkedAccountsList.append(la)
            # Migrate multi-line misc values stored as lists in older data format
            for k, v in acc.misc.items():
                if isinstance(v, list):
                    acc.misc[k] = ''.join(v)

    def updateMasterPassword(self, password: str):
        self.masterPassword = password
        self.save()
