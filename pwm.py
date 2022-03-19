from getpass import getpass
from types import FunctionType
from pwmdata import Database, Account

### High level view:
# States are used to facilitate going 'back' to the previous step. User input = '`'
# Manager navigates between states using a stack
# - upon reading states, if returns new state, adds to stack to read next
# - if no new state is returned, current state is removed from stack (equates to 'back')
### States can be: 
# 1) option-choosing states 
# - will have > 1 option in the options list to display, user enters 1/2/3/4 etc
# or 2) text-input states
# - only 1 option in the list, with option.textInput=True, user enters text input
# - if option.passwordInput=True, the getpass function will be used to hide password inputs
# a state may be dynamically generated with additional dynamic data
### Options will contain:
# 1) message string
# 2) function object that can be called to execute. 
# - This includes functions that manipulate the state stack / start other processes
# NOTE: currently built assuming it is ok to have function objects 
# directly calling data data object from within

### Notation:
# st_ prefixes are states
# fo_ prefixes are for functions to be used as function objects
# fog_ prefixes are for functions that generate function objects

class Manager:

  maxColCharWidth = 28
  totalColumns = 4
  indent = 2

  def __init__(self) -> None:
    self.stateStack = []

  # return top item of stack
  def viewStack(self):
    top = len(self.stateStack) - 1
    return self.stateStack[top]

  def pushStack(self, newState):
    self.stateStack.append(newState)

  # pops stack and returns popped
  def popStack(self, num=1):
    for i in range(0, num):
      self.stateStack.pop()

  def readStack(self):
    returnedState = self.viewStack().readState()
    if returnedState:
      self.pushStack(returnedState)
    else:
      self.popStack()

  # removes all stacks until a number of leftovers
  def flushStack(self, leftover=0):
    while len(self.stateStack) > leftover + 1:
      self.popStack()

  def run(self):
    while len(self.stateStack) > 0:
      self.readStack()

  # creating the state tree from root to branches
  def initialization(self):
    # Home state:
    st_home = State('Yo sup')
    manager.pushStack(st_home)
    
    st_addAccount = State('Adding new account')
    st_addAccount.addOption(Option('Account name: ', fo_addAccount))
    st_deleteAccount = State('Deleting account')
    st_searchByName = State('Search by Name')
    st_checkMasterPassword = State('Changing Master Password\nYou can backtrack this process with "`"')
    st_checkMasterPassword.addOption(Option('Enter current master password: ', fo_checkMasterPassword, passwordInput=True))
    
    st_home.addOption(Option('Search by Name', fog_nextState(st_searchByName)))
    st_home.addOption(Option('Add New Account', fog_nextState(st_addAccount)))
    st_home.addOption(Option('Search by Email', fo_getEmailList))
    st_home.addOption(Option('Search by Username', fo_getUsernameList))
    st_home.addOption(Option('Search by Password', fo_getPasswordList))
    st_home.addOption(Option('Search by Phone Number', fo_getPhoneList))
    st_home.addOption(Option('Search by Linked Account', fo_getLinkedAccountList))
    st_home.addOption(Option('Change Master Password', fog_nextState(st_checkMasterPassword)))
    # st_home.addOption(Option('Delete Account Entry', fog_nextState(st_deleteAccount))) TODO

    opt_inputKeyword = Option('Enter keyword to search:', fo_searchByName)
    st_searchByName.addOption(opt_inputKeyword)


class State:
  def __init__(self, displayMessage) -> None:
    self.displayMessage = displayMessage
    self.options = [] # initially empty

  def addOption(self, option):
    self.options.append(option)

  def readState(self):
    print(f'\n{self.displayMessage}')
    optionsLength = len(self.options)
    if optionsLength == 0:
      return
    # If there is only 1 option, it could be a text input state
    elif optionsLength == 1:
      if self.options[0].textInput:
        if self.options[0].passwordInput:
          text = getpass(f'{self.options[0].message}')
        else:
          text = input(f'{self.options[0].message}')
        # exception case - for going back
        if text == '`':
          printn('"Back" registered')
          return
        if text == '``':
          printn('"Exit" registered')
          manager.flushStack()
          return
        return self.options[0].execute(text)
      # 1 Option, but not for text input -> fast forward to selection
      # pop stack for double jump back
      manager.popStack()
      return self.options[0].execute()
    # Choice input states
    else:
      for n, option in enumerate(self.options):
        message = option.message[0:Manager.maxColCharWidth - Manager.indent - 1 - len(str(n + 1))]
        print(f'{n + 1}. {message}' + \
          f'{" " * max((Manager.maxColCharWidth - Manager.indent - len(str(n + 1)) - len(message) + 1), 1)}', end='')
        if n % Manager.totalColumns == Manager.totalColumns - 1 :
          print("")
      print("")
      text = input('(1/2/3/...) >>> ')
      # duplicate keys for easy reach on qwerty keyboard  
      numMapping = {
        'q': '4',
        'w': '5',
        'e': '6',
        'a': '7',
        's': '8',
        'd': '9'
      }
      if text in numMapping:
        text = numMapping[text]
    
      if text.isdigit():
        choice = int(text) - 1
        try:
          return self.options[choice].execute()
        except IndexError:
          print('Not within options given')
      elif text == '`':
        printn('"Back" registered')
        return
      elif text == '``':
        printn('"Exit" registered')
        manager.flushStack()
        return
      else:
        print(f'Invalid input: {text}')
      

class Option:
  def __init__(self, message, functionObj, textInput=True, passwordInput=False) -> None:
    if type(functionObj) != FunctionType:
      raise TypeError("Option: Function Object input is of wrong type")
    self.message = message
    self.functionObj = functionObj
    self.textInput = textInput
    self.passwordInput = passwordInput

  def execute(self, *args):
    if args:
      return self.functionObj(*args)
    return self.functionObj()

### UTIL Functions

# returns a function object that returns the next state
def fog_nextState(nextstate, accountFocused=None):
  def outputFunc():
    if accountFocused:
      nextstate.accountFocused = accountFocused
    return nextstate
  return outputFunc

# wrapper to start a new print block on CLI
def printn(text):
  print(f'\n{text}')

# function object that returns manager to home state
def fo_home():
  manager.flushStack(1)

### end of UTIL Functions

### processes (interacts with Data)

# function object that checks current master password for authentication
def fo_checkMasterPassword(text):
  if data.masterPassword == text:
    st_enterNewPass = State('Authentication Complete')
    st_enterNewPass.addOption(Option('Enter new master password: ', fo_enterNewMasterPassword, passwordInput=True))
    return st_enterNewPass
  else:
    print('The password you have entered is invalid')

def fo_enterNewMasterPassword(newPassword):
  st_confirmNewPass = State('Confirm the new password')
  st_confirmNewPass.addOption(Option('Re-enter new master password', fog_confirmNewMasterPassword(newPassword), passwordInput=True))
  return st_confirmNewPass

# function object generator that asks for password again for confirmation
def fog_confirmNewMasterPassword(password):
  def outputfunc(text):    
    if text == password:
      data.masterPassword = password
    else:
      print('password entered does not match')
    # back to home state regardless of match
    fo_home()
  return outputfunc

# function object that requests for keyword input to filter data data
# returns next state containing list of accounts filtered
def fo_searchByName(text):
  accountList = data.filterAccountsByName(text)
  st_filtered = State(f'There are {len(accountList)} matches')
  for acc in accountList:
    st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
  return st_filtered

# returns next state containing list of accounts filtered by email
def fog_getAccountsWithEmail(email):
  def outputfunc():
    accountList = data.filterAccountsByEmail(email)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
    return st_filtered
  return outputfunc

# function object that shows all emails used in accounts
def fo_getEmailList():
  st_emailList = State('Emails:')
  for email in data.emailList:
    st_emailList.addOption(Option(email, fog_getAccountsWithEmail(email), textInput=False))
  return st_emailList


# returns next state containing list of accounts filtered by username
def fog_getAccountsWithUsername(username):
  def outputfunc():
    accountList = data.filterAccountsByUsername(username)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
    return st_filtered
  return outputfunc

# function object that shows all usernames used in accounts
def fo_getUsernameList():
  st_usernameList = State('Usernames:')
  for i in data.usernameList:
    st_usernameList.addOption(Option(i, fog_getAccountsWithUsername(i), textInput=False))
  return st_usernameList

# returns next state containing list of accounts filtered by password
def fog_getAccountsWithPassword(password):
  def outputfunc():
    accountList = data.filterAccountsByPassword(password)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
    return st_filtered
  return outputfunc

# function object that shows all passwords used in accounts
def fo_getPasswordList():
  st_passwordList = State('Passwords:')
  for i in data.passwordList:
    st_passwordList.addOption(Option(i, fog_getAccountsWithPassword(i), textInput=False))
  return st_passwordList
  
# returns next state containing list of accounts filtered by phone number
def fog_getAccountsWithPhone(phone):
  def outputfunc():
    accountList = data.filterAccountsByPhone(phone)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
    return st_filtered
  return outputfunc

# function object that shows all passwords used in accounts
def fo_getPhoneList():
  st_phoneList = State('Phone Numbers:')
  for i in data.phoneList:
    st_phoneList.addOption(Option(i, fog_getAccountsWithPhone(i), textInput=False))
  return st_phoneList

# returns next state containing list of accounts filtered by name of linked account
def fog_getAccountsWithLinkedAccount(name):
  def outputfunc():
    accountList = data.filterAccountsByLinkedAccount(name)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
    return st_filtered
  return outputfunc

# function object that shows all linked accounts used in accounts
def fo_getLinkedAccountList():
  st_linkedAccountList = State('Linked Accounts:')
  for i in data.linkedAccountsList:
    st_linkedAccountList.addOption(Option(i, fog_getAccountsWithLinkedAccount(i), textInput=False))
  return st_linkedAccountList

# returns function object that calls data functions to change 
# the selected field of given account
def fog_editName(account):
  def outputfunc(text):
    updatedAccount = data.editName(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc
def fog_editEmail(account):
  def outputfunc(text):
    updatedAccount = data.editEmail(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc
def fog_editUsername(account):
  def outputfunc(text):
    updatedAccount = data.editUsername(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc
def fog_editPassword(account):
  def outputfunc(text):
    updatedAccount = data.editPassword(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc
def fog_editPhone(account):
  def outputfunc(text):
    updatedAccount = data.editPhone(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc
def fog_editLinkedAccounts(account):
  def outputfunc(text):
    updatedAccount = data.editLinkedAccounts(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc

def stringifyAccount(account):
  return \
    f'Account   : {account.name}\n'+ \
    f'username  : {account.username}\n' + \
    f'email     : {account.email}\n' + \
    f'password  : {account.password}\n' + \
    f'phone     : {account.phone}\n' + \
    f'linked Acc: {stringifyLinkedAccounts(account.linkedAccount)}\n' + \
    f'misc:\n' + \
    f'{stringifyMisc(account.misc)}'

def stringifyLinkedAccounts(la):
  output = ''
  for a in la:
    output += a + ', '
  return output[:-2]

# returns a string of the dict-type misc information variable to be printed
def stringifyMisc(misc):
  # return str(misc)
  string = ''
  for i in misc.items():
    string += f'  {i[0]}{" " * max(8 - len(i[0]), 0)}: {i[1]}\n'
  return string


# returns function object that displays given account details, 
# with next state that edits or exits
def fog_focusAccount(account):
  def outputfunc():
    st_viewAccount = State(f'{stringifyAccount(account)}\n\nWhat do?')
    st_editName = State(f'Old account name: {account.name}')
    st_editName.addOption(Option("New account name: ", fog_editName(account)))
    st_editUsername = State(f'Old account username: {account.username}')
    st_editUsername.addOption(Option("New account username: ", fog_editUsername(account)))
    st_editEmail = State(f'Old account email: {account.email}')
    st_editEmail.addOption(Option("New account email: ", fog_editEmail(account)))
    st_editPassword = State(f'Old account password: {account.password}')
    st_editPassword.addOption(Option("New account password: ", fog_editPassword(account)))
    st_editLinkeAccounts = State(f'Currently linked Accounts: {account.linkedAccount}')
    st_editLinkeAccounts.addOption(Option("Type another account name to add, write an existing name to delete\n: ", fog_editLinkedAccounts(account)))
    st_editPhone = State(f'Old Phone number: {account.phone}')
    st_editPhone.addOption(Option("New Phone number: ", fog_editPhone(account)))
    st_editMisc = State(f'What field to edit / delete? (adds if not existent)')
    st_editMisc.addOption(Option('Field name: ', fog_chooseField(account)))

    st_deleteConfirmation = State(f'Are you sure you want to delete the account for {account.name}')
    st_deleteConfirmation.addOption(Option('1 = YES \\ enter = NO: ', fog_deleteAccount(account)))

    st_viewAccount.addOption(Option('Edit Name', fog_nextState(st_editName)))
    st_viewAccount.addOption(Option('Edit Username', fog_nextState(st_editUsername)))
    st_viewAccount.addOption(Option('Edit Email', fog_nextState(st_editEmail)))
    st_viewAccount.addOption(Option('Edit Password', fog_nextState(st_editPassword)))
    st_viewAccount.addOption(Option('Edit Phone Number', fog_nextState(st_editPhone)))
    st_viewAccount.addOption(Option('Edit LinkedAccounts', fog_nextState(st_editLinkeAccounts)))
    st_viewAccount.addOption(Option('Edit Misc info', fog_nextState(st_editMisc)))
    st_viewAccount.addOption(Option('Delete Account', fog_nextState(st_deleteConfirmation)))
    st_viewAccount.addOption(Option('Exit', fo_home))
    return st_viewAccount
  return outputfunc

# function object that adds an account with input name to database,
# returns with a state focusing on data. input name must not previously exist
def fo_addAccount(text):
  if not data.checkNameExists(text):
    acc = data.addAccount(Account(name=text))
    return fog_focusAccount(acc)()
  else:
    print(f'Account with name "{text}" already exists')

# returns a function object that takes 1 as input confirmation to delete selected acc
def fog_deleteAccount(acc):
  def outputfunc(input):
    if input == '1':
      data.deleteAccount(acc)
      fo_home()
  return outputfunc

# returns a function object that asks for field to edit
# field exists: next state asks for new value, field doesn't exist: add key
def fog_chooseField(acc):
  def outputfunc(field):
    if field in acc.misc:
      st_editField = State(f'Old value: {acc.misc[field]}')
      st_editField.addOption(Option('New value: ', fog_editField(acc, field)))
      return st_editField
    else:
      st_addField = State(f'To add field: {field}')
      st_addField.addOption(Option('Value: ', fog_editField(acc, field)))
      return st_addField
  return outputfunc

# generates function object updates the misc field with requested value
# if value is empty, field is deleted. Handled internally by data
def fog_editField(acc, field):
  def outputfunc(value):
    updatedAcc = data.editMiscField(acc, field, value)
    manager.popStack(3)
    return fog_focusAccount(updatedAcc)()
  return outputfunc

### end of processes


if __name__ == '__main__':

  # Init Options and States
  print('Password Manager running...')
  data = Database()
  
  if data.load():
    manager = Manager()
    manager.initialization()
    manager.run()
    data.save()

  print("Exiting Password Manager")
