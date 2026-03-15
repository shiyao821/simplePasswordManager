import os
import json
from json import JSONEncoder
from base64 import urlsafe_b64encode
from copy import copy
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from datetime import datetime as dt
import datetime

### Data module for pwm.py
# Abstracts data operations away from UX concerns.

# --- File format ---
# New format:  [4-byte magic][32-byte random salt][Fernet ciphertext]
# Legacy format: raw Fernet ciphertext (detected by absence of magic header)
_FILE_MAGIC  = b'PWM\x01'
_SALT_LENGTH = 32

# Legacy constants — kept only for reading old files
_LEGACY_SALT           = b'69420'
_LEGACY_KDF_ITERATIONS = 69420


def _derive_key_legacy(password: str) -> bytes:
    """PBKDF2-based key derivation. Used only to decrypt legacy data files."""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_LEGACY_SALT, iterations=_LEGACY_KDF_ITERATIONS)
    return urlsafe_b64encode(kdf.derive(password.encode('utf-8')))


def derive_key(password: str, salt: bytes) -> bytes:
    """Argon2id key derivation. salt must be a 32-byte random value."""
    kdf = Argon2id(salt=salt, length=32, iterations=3, lanes=4, memory_cost=65536)
    return urlsafe_b64encode(kdf.derive(password.encode('utf-8')))


def decrypt_file_data(raw: bytes, password: str) -> tuple[bytes, bytes | None]:
    """
    Decrypt raw file bytes using the appropriate format.
    Returns (plaintext, salt). salt is None for legacy-format files — a fresh
    salt will be generated automatically on the next save.
    """
    if raw[:len(_FILE_MAGIC)] == _FILE_MAGIC:
        offset    = len(_FILE_MAGIC)
        salt      = raw[offset : offset + _SALT_LENGTH]
        ciphertext = raw[offset + _SALT_LENGTH :]
        return Fernet(derive_key(password, salt)).decrypt(ciphertext), salt
    else:
        # Legacy format: raw Fernet token encrypted with PBKDF2 + hardcoded salt
        return Fernet(_derive_key_legacy(password)).decrypt(raw), None


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
        self._salt: bytes | None = None
        self.accountList: list[Account] = []
        self.usernameList: list[str] = []
        self.emailList: list[str] = []
        self.passwordList: list[str] = []
        self.phoneList: list[str] = []
        self.linkedAccountsList: list[str] = []

    def load(self, password: str):
        with open(self.DATA_FILE_NAME, 'rb') as f:
            raw = f.read()
        self.masterPassword = password
        decrypted, salt = decrypt_file_data(raw, password)
        if salt is None:
            # Legacy file detected — generate a new salt and migrate immediately
            print("Migrating data file to new secure format (Argon2id + random salt)...")
            self._salt = os.urandom(_SALT_LENGTH)
        else:
            self._salt = salt
        for line in decrypted.splitlines():
            acc = Account(**json.loads(line.decode('utf-8'), object_hook=decode_datetime))
            self.accountList.append(acc)
        self.updateLists()
        if salt is None:
            self.save()
            print("Migration complete.")
        return self

    def save(self):
        self.sortAlphaNumeric()
        self.updateLists()
        if self._salt is None:
            self._salt = os.urandom(_SALT_LENGTH)
        json_lines = '\n'.join(json.dumps(acc.__dict__, cls=DateTimeEncoder) for acc in self.accountList) + '\n'
        encrypted = Fernet(derive_key(self.masterPassword, self._salt)).encrypt(json_lines.encode('ascii'))
        with open(self.DATA_FILE_NAME, 'wb') as f:
            f.write(_FILE_MAGIC + self._salt + encrypted)

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

    def importData(self, filename: str, password: str) -> tuple[int, int]:
        """
        Import and merge accounts from another data file.
        - New accounts (by accountName) are added.
        - Duplicate accounts are replaced only if the imported copy is newer.
        Returns (added_count, updated_count).
        Raises InvalidToken if the password is wrong.
        """
        with open(filename, 'rb') as f:
            raw = f.read()
        decrypted, _ = decrypt_file_data(raw, password)

        # Build an index of current accounts for O(1) lookup
        existing = {acc.accountName: i for i, acc in enumerate(self.accountList)}
        added = 0
        updated = 0

        for line in decrypted.splitlines():
            if not line.strip():
                continue
            imported = Account(**json.loads(line.decode('utf-8'), object_hook=decode_datetime))
            if not imported.accountName:
                continue
            if imported.accountName in existing:
                idx = existing[imported.accountName]
                if imported.lastEdited > self.accountList[idx].lastEdited:
                    self.accountList[idx] = imported
                    updated += 1
            else:
                self.accountList.append(imported)
                existing[imported.accountName] = len(self.accountList) - 1
                added += 1

        if added > 0 or updated > 0:
            self.save()
        return added, updated
