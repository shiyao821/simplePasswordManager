import os
import json
import copy

### this version is to be used together with hashv2.py
# It is repurposed to serve as the data module, abstracts away data operations and removes UX operations

# Init and counters
MASTER_FILE_NAME = 'acc.pkl'
MASTER_JSON_NAME = 'acc.json'
master = None

class Database():
  def __init__(self, accountList=[], emailList=[], usernameList=[], passwordList=[], phoneList=[], linkedAccountList=[]):
    # the following list should be unique at all times.
    # current update operations: see def updateLists
    self.accountList = accountList
    self.usernameList = usernameList
    self.emailList = emailList
    self.passwordList = passwordList
    self.phoneList = phoneList
    self.linkedAccountList = linkedAccountList # entries will be the string in Account.name

  # load data from some file in same directory
  def load(self):
    with open(MASTER_JSON_NAME, 'r') as inJson:
      while json_string := inJson.readline():
        acc = Account(**json.loads(json_string))
        self.accountList.append(acc)
      self.updateLists()
    return self

  # save data to file
  def save(self):
    self.sortAlphaNumeric()
    self.updateLists()
    with open(MASTER_JSON_NAME, 'w') as outJson:
      for acc in self.accountList:
        json_string = json.dumps(acc.__dict__)
        outJson.write(json_string + '\n')
        
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
    return list(filter(lambda a: a.linkedAccount == name, self.accountList))
  
  # adds a given account with a non-empty name to the database, and returns it
  def addAccount(self, account):
    if not account.name == '':
      self.accountList.append(account)
      self.save()
    return account

  # given an Account, delete it from the database
  def deleteAccount(self, account):
    accountName = copy.copy(account.name)
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
    # check uniqueness
    if self.checkNameExists(text):
      self.accountList.remove(account.name)
      account.name = text
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
  def editLinkedAccount(self, account, text):
    # check that account exists:
    if text not in [acc.name for acc in self.accountList]:
      print(f'Account to be linked does not exist yet. Create it first.')
      return account
    account.linkedAccount = text
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
    self.linkedAccountList = []

    for acc in self.accountList:
      if acc.username not in self.usernameList:
        self.usernameList.append(acc.username)
      if acc.email not in self.emailList:
        self.emailList.append(acc.email)
      if acc.password not in self.passwordList:
        self.passwordList.append(acc.password)
      if acc.phone not in self.phoneList:
        self.phoneList.append(acc.phone)
      if acc.linkedAccount not in self.linkedAccountList:
        self.linkedAccountList.append(acc.linkedAccount)

class Account():
  def __init__(self, name='', username='', email='', password='', phone='', linkedAccount='', misc={}):
    self.name = name
    self.username = username
    self.email = email
    self.password = password
    self.phone = phone
    self.linkedAccount = linkedAccount
    self.misc = misc

def dataScript():
  # for i in master.usernameList:
  #   print(i)
  # for i, a in enumerate(master.linkedAccountList):
  #   print(i, a)

  for acc in master.accountList:
    new = {}
    new['legacy'] = acc.misc
    acc.misc = new

  #   if isinstance(account.username, int):
  #     account.username = master.usernameList[account.username]
  #   if isinstance(account.linkedAccount, int):
  #     account.linkedAccount = master.linkedAccountList[account.linkedAccount]
  #   if isinstance(account.email, int):
  #     account.email = master.emailList[account.email]
  #   if isinstance(account.password, int): 
  #     account.password = master.passwordList[account.password]
    
    # f.write(f'===================================\n')
    # f.write(f'Account : {account.name}\n')
    # f.write(f'username: {account.username}\n')
    # f.write(f'email   : {account.email}\n')
    # f.write(f'password: {account.password}\n')
    # if not isinstance(account.username, int):
    #   master.editUsername(account, account.username)
    # if not isinstance(account.linkedAccount, int):
    #   master.editLinkedAccount(account, account.linkedAccount)

if __name__ == '__main__':

  master = Database()
  # check if previous dump file exists
  if os.path.isfile(MASTER_FILE_NAME):
    with open(MASTER_FILE_NAME, 'rb') as inFile:
      master.load()  
  else:
    print(f'New master file {MASTER_FILE_NAME} created')

  command = input('\
    Proceed with Script?\n\
    (1 for yes): ')
  if command == 'y':
    dataScript()
    print('script completed')
  else:
    print('bye')
  # save at the end of 1 operation
  master.save()