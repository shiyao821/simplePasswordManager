import os
import pickle
import copy

### this version is to be used together with hashv2.py
# It is repurposed to serve as the data module, abstracts away data operations and removes UX operations

### TODO:
# currently the info stored are index pointer based. FK
# I thought this would be cool and greatly accelerate referencing
# But this means that there is no way of removing items within the lists without large amounts of work
# to change the info stored to HARD TEXT

# Init and counters
MASTER_FILE_NAME = 'acc.pkl'
master = None

class Master():
  def __init__(self):
    self.emailList = []
    self.passwordList = []
    self.accountList = []
    self.usernameList = []
    self.linkedAccountList = [] # entries will be the string in Account.name
    self.filteredAccountList = [] # a view to show only filtered accounts (contains exact same objects as accountList)

  # returns number of accounts in data
  def numAccounts(self):
    return len(self.accountList)

  # util function for internal account list sorting
  def sortAlphaNumeric(self, reverse=False):
    self.accountList.sort(key=lambda a: a.name, reverse=reverse)

  # returns correct number pointer in given list after updating list with input text if necessary
  def getNumPointer(self, acclist, text):
    try:
      pointer = acclist.index(text)
    except ValueError:
      acclist.append(text)
      pointer = len(acclist) - 1
    return pointer
    
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
    ptr = self.getNumPointer(self.emailList, email)
    return list(filter(lambda a: a.email == ptr, self.accountList))
  # returns a list of Accounts using given username, assuming it exists
  def filterAccountsByUsername(self, username):
    ptr = self.getNumPointer(self.usernameList, username)
    return list(filter(lambda a: a.username == ptr, self.accountList))
  # returns a list of Accounts using given password, assuming it exists
  def filterAccountsByPassword(self, password):
    ptr = self.getNumPointer(self.passwordList, password)
    return list(filter(lambda a: a.password == ptr, self.accountList))
  # returns a list of Accounts using given account name, assuming it exists
  def filterAccountsByLinkedAccount(self, name):
    ptr = self.getNumPointer(self.linkedAccountList, name)
    return list(filter(lambda a: a.linkedAccount == ptr, self.accountList))
  
  # adds a given account with a non-empty name to the database, and returns it
  def addAccount(self, account):
    if not account.name == '':
      self.accountList.append(account)
    return account

  # given an Account, delete it from the database
  def deleteAccount(self, account):
    accountName = copy.copy(account.name)
    if prompt(f'Are you sure you want to delete the account for {accountName}'):
      # search for account in the actual list
      for acc in self.accountList:
        if acc == account:
          self.accountList.remove(acc)
          del acc
          print(f'Account for {accountName} deleted')
          break

  # given an Account, returns Account edited
  def editName(self, account, text):
    # check uniqueness
    if text not in [acc.name for acc in self.accountList]:
      self.accountList.remove(account.name)
      account.name = text
    print(f'Input name {text} already exists')
    return account
    
  # given an Account, returns Account edited
  def editUsername(self, account, text):
    account.username = self.getNumPointer(self.usernameList, text)
    return account

  # given an Account, returns Account edited
  def editEmail(self, account, text):
    account.email = self.getNumPointer(self.emailList, text)
    return account

  # given an Account, returns Account edited
  def editPassword(self, account, text):
    account.password = self.getNumPointer(self.passwordList, text)
    return account
    
  # given an Account, returns Account edited
  def editLinkedAccount(self, account, text):
    account.linkedAccount = self.getNumPointer(self.linkedAccountList, text)
    return account

  # # LEGACY
  # def viewAccount(self, index, showDetails=False):
  #   account = self.filteredAccountList[index]
  #   print(f'Account : {account.name}')
  #   print(f'username: {account.username}')
  #   print(f'email   : {self.emailList[account.email]}')
  #   print(f'password: {self.passwordList[account.password]}')
  #   if showDetails or prompt('more details?'):
  #     print('misc ================================')
  #     for line in account.misc:
  #       print(line, end='')
  #     print('\n=====================================')



class Account():
  def __init__(self):
    self.name = ''
    self.username = ''
    self.email = ''
    self.password = ''
    self.linkedAccount = ''
    self.misc = {} # TODO: convert to dict


def prompt(question):
  print(question, end=' (1 = YES \\ enter = NO) ')
  i = input()
  return i == '1'

# return a subset string list filtering by first letter of string
def sublist(list, letter):
  return filter(lambda e: e[0] == letter.upper() or e[0] == letter.lower(), list)

def viewAllData():
  with open('allData.txt', 'w') as f:
    for account in master.accountList:

      # if not isinstance(account.email, int):
      #   print(f'{account.name} email in plain text')
      # if not isinstance(account.password, int): 
      #   print(f'{account.name} password in plain text : {account.password}')
      # f.write(f'===================================\n')
      # f.write(f'Account : {account.name}\n')
      # f.write(f'username: {account.username}\n')
      # f.write(f'email   : {account.email}\n')
      # f.write(f'password: {account.password}\n')
      if not isinstance(account.username, int):
        master.editUsername(account, account.username)
      if not isinstance(account.linkedAccount, int):
        master.editLinkedAccount(account, account.linkedAccount)

def numberInput(string):
  text = input(string)
  if text.isdigit():
    return int(text)
  else:
    print(f'Invalid input: {text}')
    return -1

def deleteAccounts():
  if prompt('List Accounts?'):
    master.listAccounts()
  index = numberInput('Enter index number of acount to delete: ')
  master.deleteAccount(index - 1)

def saveMasterFile(master):
  master.sortAlphaNumeric()
  with open(MASTER_FILE_NAME, 'wb') as outFile:
    pickle.dump(master, outFile, pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':

  # check if previous dump file exists
  if os.path.isfile(MASTER_FILE_NAME):
    with open(MASTER_FILE_NAME, 'rb') as inFile:
      master = pickle.load(inFile)
      master.sortAlphaNumeric()
      print(f'Master file {MASTER_FILE_NAME} with {master.numAccounts()} accounts found')
  else:
    master = Master()
    print(f'New master file {MASTER_FILE_NAME} created')

  while True:
    command = input('\
      What to do?\n\
      1. view accounts\n\
      2. add account\n\
      3. transfer accounts\n\
      4. delete account entry\n\
      5. edit account entry\n\
      6. exit\n\
      (1\\2\\3\\...): ')
    if command == '1':
      if prompt('List Accounts?'):
        master.listAccounts()
      index = numberInput('Enter index number to show acc details: ')
      master.viewAccount(index - 1)
    elif command == '2':
      temp = input('Any misc information: ')
      master.addAccount(temp)
    elif command == '3':
      viewAllData()
    elif command == '4':
      deleteAccounts()
    elif command == '5':
      if prompt('List Accounts?'):
        master.listAccounts()
      index = numberInput('Enter index of account to edit: ')
      master.editAccount(index - 1)
    elif command == '6':
      break
    else:
      print('didn\'t understand input')

    # save at the end of 1 operation
    saveMasterFile(master)
  
  saveMasterFile(master)