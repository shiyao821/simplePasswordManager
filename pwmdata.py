import json
from base64 import urlsafe_b64encode
from getpass import getpass
from copy import copy
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

### this version is to be used together with pwm.py
# It is repurposed to serve as the data module, abstracts away data operations and removes UX operations

DATA_FILE_NAME = 'accounts.data'

class Database():
  def __init__(self, accountList=[], emailList=[], usernameList=[], passwordList=[], phoneList=[], linkedAccountList=[]):
    self.masterPassword = ''
    self.accountList = accountList
    self.usernameList = usernameList
    self.emailList = emailList
    self.passwordList = passwordList
    self.phoneList = phoneList
    self.linkedAccountsList = linkedAccountList # entries will be the string in Account.name

  # load data from some file in same directory
  def load(self):
    try:
      with open(DATA_FILE_NAME, 'rb') as inputFile:
        encrypted = inputFile.read()
        # Save input password for encryption later
        self.masterPassword = getpass("Please enter your password: ")
        # decrypt file based on self.masterPassword
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'69420', iterations=69420)
        key = urlsafe_b64encode(kdf.derive(bytes(self.masterPassword, 'utf-8')))
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted)

        for line in decrypted.splitlines():
          acc = Account(**json.loads(str(line, 'utf-8')))
          self.accountList.append(acc)
        self.updateLists()
      return self
    except InvalidToken:
      print('The password you have entered is invalid')
      return
    except FileNotFoundError:
      print(f'Data file {DATA_FILE_NAME} does not exist. \n' + \
        'It seems like this is your first time using the program.')
      self.masterPassword = input("Please setup a password: ")
      return self

  # save data to file
  def save(self):
    self.sortAlphaNumeric()
    self.updateLists()
    with open(DATA_FILE_NAME, 'wb') as outputFile:
      json_string = ''
      for acc in self.accountList:
        json_string += json.dumps(acc.__dict__) + '\n'

      # encrypt based on self.masterPassword 
      kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'69420', iterations=69420)
      key = urlsafe_b64encode(kdf.derive(bytes(self.masterPassword, 'utf-8')))
      fernet = Fernet(key)
      
      encrypted = fernet.encrypt(bytes(json_string, 'ascii'))
      outputFile.write(encrypted)

  # returns number of accounts in data
  def numAccounts(self):
    return len(self.accountList)

  # util function for internal account list sorting
  def sortAlphaNumeric(self, reverse=False):
    self.accountList.sort(key=lambda a: a.name, reverse=reverse)

  # returns a list of Accounts containing keyword. 
  # If keyword is a single letter, checks only for first letter
  # If keyword is blank, return all. Can return empty list.
  def filterAccountsByName(self, keyword): 
    if len(keyword) == 1:
      filteredList = filter(lambda account: keyword == account.name[0], self.accountList)
    else:
      filteredList = filter(lambda account: keyword in account.name, self.accountList)
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
  def filterAccountsByLinkedAccount(self, name):
    return list(filter(lambda a: name in a.linkedAccount, self.accountList))
  
  # adds a given account with a non-empty name to the database, and returns it
  def addAccount(self, account):
    if not account.name == '':
      self.accountList.append(account)
      self.save()
    return account

  # given an Account, delete it from the database
  def deleteAccount(self, account):
    accountName = copy(account.name)
    # search for account in the actual list
    for acc in self.accountList:
      if acc == account:
        self.accountList.remove(acc)
        del acc
        print(f'Account for {accountName} deleted')
        break
    self.save()

  # check if account name exists
  def checkNameExists(self, name):
    return name in [acc.name for acc in self.accountList]

  # given an Account, returns Account edited
  def editName(self, account, text):
    if not text:
      print(f'Cannot enter empty name')
    # check uniqueness
    if not self.checkNameExists(text):
      account.name = text
    else:
      print(f'Input name {text} already exists')
    return account
    
  # given an Account, returns Account edited
  def editUsername(self, account, text):
    account.username = text
    self.save()
    return account

  # given an Account, returns Account edited
  def editEmail(self, account, text):
    account.email = text
    self.save()
    return account

  # given an Account, returns Account edited
  def editPassword(self, account, text):
    account.password = text
    self.save()
    return account

  # given an Account, returns Account edited
  def editPhone(self, account, text):
    if not self.isPhoneNumber(text):
      print(f'Text entered {text} is not of phone number format (accepts numbers and "+" only)')
      return account
    account.phone = text
    self.save()
    return account
    
  # given an Account, returns Account edited
  # if name given does not currently exist in list, add
  # if it currently exists in list, delete
  def editLinkedAccounts(self, account, text):
    if text in account.linkedAccount:
      account.linkedAccount.remove(text)
    else:
      # check that account exists:
      if text not in [acc.name for acc in self.accountList]:
        print(f'Account to be linked does not exist yet. Create it first.')
        return account
      account.linkedAccount.append(text)
    self.save()
    return account

  # given an account, update the misc field. Deletes key-value pair if 'value' is empty
  def editMiscField(self, acc, field, value):
    if value == '':
      del acc.misc[field]
    else:
      acc.misc[field] = value
    return acc

  # given a text, check if is of phone format:
  def isPhoneNumber(self, text):
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
      for la in acc.linkedAccount:
        if la not in self.linkedAccountsList:
          self.linkedAccountsList.append(la)

class Account():
  def __init__(self, name='', username='', email='', password='', phone='', linkedAccount=[], misc={}):
    self.name = name
    self.username = username
    self.email = email
    self.password = password
    self.phone = phone
    self.linkedAccount = linkedAccount
    self.misc = misc
