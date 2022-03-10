import os
import pickle
import copy

# Init and counters
MASTER_FILE_NAME = 'acc.pkl'
master = None
FILE_READ_LIMIT = -1
filePointer = 0

class Master():
  def __init__(self):
    self.emailList = []
    self.passwordList = []
    self.accountList = []
    self.filteredAccountList = [] # a view to show only filtered accounts (contains exact same objects as accountList)

  # populates self.filteredAccountList using the iterator returned by the filter() function
  def fillFilteredAccountsList(self, iterator):
    # reset filtered List
    self.filteredAccountList = []
    # populate with iterator
    while True:
      try: 
        self.filteredAccountList.append(next(iterator))
      except StopIteration:
        break

  def sortAlphaNumeric(self, reverse=False):
    self.accountList.sort(key=lambda a: a.name, reverse=reverse)
  
  def listAccounts(self):
    if prompt('Filter by first character?'):
      char = input('Character to filter by: ')
      if not char.isalpha():
        print(f'Input character is not an alphabet: {char}')
        return
      self.fillFilteredAccountsList(filter(lambda a: a.name[0] == char, self.accountList))
    else:
      self.filteredAccountList = self.accountList
    for i, acc in enumerate(self.filteredAccountList):
      print(f'{i + 1}: {acc.name}')

  def numAccounts(self):
    return len(self.accountList)

  def searchAccountByName(self, name):
    self.fillFilteredAccountsList(filter(lambda a: name in a.name, self.accountList))
    self.listAccounts(self.filteredAccountList)

  def viewAccount(self, index, showDetails=False):
    account = self.filteredAccountList[index]
    print(f'Account : {account.name}')
    print(f'username: {account.username}')
    print(f'email   : {self.emailList[account.email]}')
    print(f'password: {self.passwordList[account.password]}')
    if showDetails or prompt('more details?'):
      print('misc ================================')
      for line in account.misc:
        print(line, end='')
      print('\n=====================================')

  def addEmail(self):
    email = input('email:')
    if email not in self.emailList:
      self.emailList.append(email)
    return self.emailList.index(email)

  def addPassword(self):
    password = input('password:')
    if password not in self.passwordList:
      self.passwordList.append(password)
    return self.passwordList.index(password)

  def addAccount(self, misc=None):
    name = input('account name:')
    username = input('username: ')
    emailPointer = self.addEmail()
    passwordPointer = self.addPassword()
    account = Account(name, username, emailPointer, passwordPointer, misc)
    self.accountList.append(account)

  def deleteAccount(self, index):
    account = self.filteredAccountList[index]
    accountName = copy.copy(account.name)
    if prompt(f'Are you sure you want to delete the account for {accountName}'):
      # search for account in the actual list
      for acc in self.accountList:
        if acc == account:
          self.accountList.remove(acc)
          del acc
          print(f'Account for {accountName} deleted')
          break
  
  def editAccount(self, index):
    account = self.filteredAccountList[index]
    self.viewAccount(index, True)
    print(f'What to do?\
      1. change password\n\
      2. change email\n\
      3. change username\n\
      4. add misc details\n\
      5. change account name\n\
      6. quit')
    command = input()
    if command == '1':
      account.editPassword()
    elif command == '2':
      account.editEmail()
    elif command == '3':
      account.editUsername()
    elif command == '4':
      print('New misc details (use enter for new line, enter q to quit): ')
      while True:
        text = input()
        if text == 'q':
          break
        account.misc.append(text)
    elif command == '5':
      account.editName()
    elif command == '6':
      pass
    else:
      print('didn\'t understand input')


class Account():
  def __init__(self, name, username, email, password, misc):
    self.name = name
    self.username = username
    self.email = email
    self.password = password
    self.misc = misc
  
  def log(self, details):
    print(f'Name: {self.name} \
      email: {self.email} \
      password: {self.password}')
    if details:
      print(f'misc {self.misc}')

  def editName(self):
    print(f'Old account name: {self.name}')
    self.name = input("New account name: ")
  def editPassword(self):
    print(f'Old account password: {self.password}')
    self.password = input("New account password: ")
  def editEmail(self):
    print(f'Old account email: {self.email}')
    self.email = input("New account email: ")
  def editUsername(self):
    print(f'Old account username: {self.username}')
    self.password = input("New account username: ")

def prompt(question):
  print(question, end=' (1 = YES \\ enter = NO) ')
  i = input()
  return i == '1'

# return a subset string list filtering by first letter of string
def sublist(list, letter):
  return filter(lambda e: e[0] == letter.upper() or e[0] == letter.lower(), list)

def transferAccounts():
  fileReadCount = 0
  filenames = os.listdir()
  if prompt('Filter by first character?'):
    filenames = sublist(filenames, input('character to filter by:'))
  for filename in filenames:
    if fileReadCount == FILE_READ_LIMIT:
      break
    
    if prompt(f'To open {filename}?'):
      with open(filename, 'r', encoding='utf-8') as file:
        fileReadCount += 1
        print(f'\n===========================\n opened: {filename} \n===========================')
        data = file.readlines()
        for line in data:
          print(line, end='')
        print('\n')
        if prompt(f'Add new account to master file?'):
          master.addAccount(misc=data)
        if prompt('Back to main menu?'):
          break

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
      transferAccounts()
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