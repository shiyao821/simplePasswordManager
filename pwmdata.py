import json
from json import JSONEncoder
from base64 import urlsafe_b64encode
from copy import copy
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime as dt
import datetime

### this version is to be used together with pwm.py
# It is repurposed to serve as the data module, abstracts away data operations and removes UX operations

class Account():
  def __init__(self, accountName='', username='', email='', password='', phone='', linkedAccounts=[], misc={}, lastEdited=dt.now()):
    self.accountName = accountName
    self.username = username
    self.email = email
    self.password = password
    self.phone = phone
    self.linkedAccounts = linkedAccounts
    self.misc = misc
    self.lastEdited = lastEdited


class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()

# custom Decoder
def DecodeDateTime(empDict):
  if 'lastEdited' in empDict:
    empDict["lastEdited"] = dt.fromisoformat(empDict["lastEdited"])
  return empDict

class EmptyInputException(Exception):
  def __init__(self) -> None:
      super().__init__()

class Database():
  def __init__(self, accountList=[], emailList=[], usernameList=[], passwordList=[], phoneList=[], linkedAccountsList=[]):
    self.masterPassword = ''
    self.accountList: type[list[Account]] = accountList
    self.usernameList = usernameList
    self.emailList = emailList
    self.passwordList = passwordList
    self.phoneList = phoneList
    self.linkedAccountsList = linkedAccountsList # entries will be the string in Account.accountName
    self.DATA_FILE_NAME = 'accounts.data'
    # self.TEST_FILE_NAME = 'accounts.test'

  # load data from some file in same directory
  def load(self, password):
    with open(self.DATA_FILE_NAME, 'rb') as inputFile:
      encrypted = inputFile.read()
      # Save input password for encryption later
      self.masterPassword = password
      # decrypt file based on self.masterPassword
      kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'69420', iterations=69420)
      key = urlsafe_b64encode(kdf.derive(bytes(self.masterPassword, 'utf-8')))
      fernet = Fernet(key)
      decrypted = fernet.decrypt(encrypted)

      for line in decrypted.splitlines():
        acc = Account(**json.loads(str(line, 'utf-8'), object_hook=DecodeDateTime))
        self.accountList.append(acc)
      self.updateLists()
    return self

  # save data to file
  def save(self):
    self.sortAlphaNumeric()
    self.updateLists()
    with open(self.DATA_FILE_NAME, 'wb') as outputFile:
    # with open(self.TEST_FILE_NAME, 'wb') as outputFile:
      json_string = ''
      for acc in self.accountList:
        json_string += json.dumps(acc.__dict__, cls=DateTimeEncoder) + '\n'

      # encrypt based on self.masterPassword 
      kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'69420', iterations=69420)
      key = urlsafe_b64encode(kdf.derive(bytes(self.masterPassword, 'utf-8')))
      fernet = Fernet(key)
      
      encrypted = fernet.encrypt(bytes(json_string, 'ascii'))
      outputFile.write(encrypted)
      # outputFile.write(json_string.encode('utf-8'))

  # returns number of accounts in data
  def numAccounts(self):
    return len(self.accountList)

  # util function for internal account list sorting
  def sortAlphaNumeric(self, reverse=False):
    self.accountList.sort(key=lambda a: a.accountName, reverse=reverse)

  # returns a list of Accounts containing keyword. 
  # If keyword is a single letter, checks only for first letter
  # If keyword is blank, return all. Can return empty list.
  def filterAccountsByAccountName(self, keyword): 
    if len(keyword) == 1:
      filteredList = filter(lambda account: keyword == account.accountName[0], self.accountList)
    else:
      filteredList = filter(lambda account: keyword in account.accountName, self.accountList)
    return list(filteredList)

  # returns a list of Accounts using given email, assuming it exists
  def filterAccountsByEmail(self, email):
    return list(filter(lambda a: a.email == email, self.accountList))
  # returns a list of Accounts using given username, assuming it exists
  def filterAccountsByUsername(self, username):
    return list(filter(lambda a: a.username == username, self.accountList))
  # returns a list of Accounts using given password, assuming it exists
  def filterAccountsByPassword(self, password):
    return list(filter(lambda a: a.password == password, self.accountList))
    # returns a list of Accounts using given phone number, assuming it exists
  def filterAccountsByPhone(self, phone):
    return list(filter(lambda a: a.phone == phone, self.accountList))
  # returns a list of Accounts using given account name, assuming it exists
  def filterAccountsByLinkedAccounts(self,accountName):
    return list(filter(lambda a:accountName in a.linkedAccounts, self.accountList))
  
  # adds a given account with a non-empty accountName to the database, and returns it
  def addAccount(self, account: type[Account]):
    if not account.accountName == '':
      self.accountList.append(account)
      self.save()
    return account

  # given an Account, delete it from the database
  def deleteAccount(self, account: type[Account]):
    accountName = copy(account.accountName)
    # search for account in the actual list
    for acc in self.accountList:
      if acc == account:
        self.accountList.remove(acc)
        del acc
        print(f'Account for {accountName} deleted')
        break
    self.save()

  # check if account name exists
  def checkAccountNameExists(self, name):
    return name in [acc.accountName for acc in self.accountList]

  # given an Account, returns Account edited
  def editAccountName(self, account: type[Account], text):
    if not text:
      print(f'Cannot enter empty account name')
    # check uniqueness
    if not self.checkAccountNameExists(text):
      oldName, account.accountName = account.accountName, text
      account.lastEdited = dt.now()
      self.accountList
      self.updateAllLinkedAccountInstances(oldName, text)
      self.save()
    else:
      print(f'Input name {text} already exists')
    return account
  
  def updateAllLinkedAccountInstances(self, oldName, newName):
    for acc in self.accountList:
      if oldName in acc.linkedAccounts:
        # print(f'linkedAccount found in {acc.accountName}: {acc.linkedAccounts}')
        newAccounts = list(map(lambda la: newName if la == oldName else la, acc.linkedAccounts))
        acc.linkedAccounts = newAccounts
    
  # given an Account, returns Account edited
  def editUsername(self, account: type[Account], text):
    account.username = text
    account.lastEdited = dt.now()
    self.save()
    return account

  # given an Account, returns Account edited
  def editEmail(self, account: type[Account], text):
    account.email = text
    account.lastEdited = dt.now()
    self.save()
    return account

  # given an Account, returns Account edited
  def editPassword(self, account: type[Account], text):
    account.password = text
    account.lastEdited = dt.now()
    self.save()
    return account

  # given an Account, returns Account edited
  def editPhone(self, account: type[Account], text):
    if not text:
      raise EmptyInputException
    if not self.isPhoneNumber(text):
      print(f'Text entered {text} is not of phone number format (accepts numbers and "+" only)')
      return account
    account.phone = text
    account.lastEdited = dt.now()
    self.save()
    return account
    
  # given an Account, returns Account edited
  # if accountName given does not currently exist in list, add
  # if it currently exists in list, delete
  def editLinkedAccounts(self, account: type[Account], text):
    if text in account.linkedAccounts:
      account.linkedAccounts.remove(text)
    else:
      # check that account exists:
      if text not in [acc.accountName for acc in self.accountList]:
        print(f'Account to be linked does not exist yet. Create it first.')
        return account
      account.linkedAccounts.append(text)
      account.lastEdited = dt.now()
    self.save()
    return account

  # given an account, update the miscList field. Deletes key-value pair if 'value' is empty
  def editMiscField(self, account: type[Account], field, value):
    if value == '':
      del account.misc[field]
    else:
      account.misc[field] = value
    account.lastEdited = dt.now()
    self.save()
    return account

  # given a text, check if is of phone format:
  def isPhoneNumber(self, text):
    if not text:
      return
    if text[0] == '+':
      text = text[1:]
    return text.isnumeric()

  # updates accumulation lists
  def updateLists(self):
    # clear lists
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
      
      # converts from previous data implementation where mutli-line misc items are in lists
      for k,v in acc.misc.items():
        if isinstance(v, list):
          nlValue = "".join(v)
          acc.misc[k] = nlValue

  def updateMasterPassword(self, password):
    self.masterPassword = password
    self.save()
