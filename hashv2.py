from types import FunctionType
from hashv1 import Master, Account
import hashv1

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
# a state may be dynamically generated with additional dynamic data
### Options will contain:
# 1) message string
# 2) function object that can be called to execute. 
# - This includes functions that manipulate the state stack / start other processes
# NOTE: currently built assuming it is ok to have function objects 
# directly calling master data object from within

### Notation:
# st_ prefixes are states
# fo_ prefixes are for functions to be used as function objects
# fog_ prefixes are for functions that generate function objects

class Manager:

  columnCharWidth = 25
  totalColumns = 4

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
    printn('Closing Manager')

  # creating the state tree from root to branches
  def initialization(self):
    # Home state:
    st_home = State('Yo sup')
    manager.pushStack(st_home)
    
    st_addAccount = State('Adding new account')
    st_deleteAccount = State('deleting account')
    st_searchByName = State('Search Accounts by Name')
    
    opt_searchByName = Option('Search Accounts by Name', fog_nextState(st_searchByName))
    opt_searchByEmail = Option('Search Accounts by Email', fo_getEmailList)
    opt_searchByUsername = Option('Search Accounts by Username', fo_getUsernameList)
    opt_searchByPassword = Option('Search Accounts by Password', fo_getPasswordList)
    opt_searchByLinkedAccount = Option('Search Accounts by Linked Account', fo_getLinkedAccountList)

    st_home.addOption(opt_searchByName)
    st_home.addOption(opt_searchByEmail)
    st_home.addOption(opt_searchByUsername)
    st_home.addOption(opt_searchByPassword)
    st_home.addOption(opt_searchByLinkedAccount)

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
      for n, option in enumerate(self.options, start=1):
        print(f'{n}. {option.message}')
      text = input('(1/2/3/...) >>> ')
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
  def __init__(self, message, functionObj, textInput=True) -> None:
    if type(functionObj) != FunctionType:
      raise TypeError("Option: Function Object input is of wrong type")
    self.message = message
    self.functionObj = functionObj
    self.textInput = textInput

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

# function object that requests for keyword input to filter master data
# returns next state containing list of accounts filtered
def fo_searchByName(text):
  accountList = master.filterAccountsByName(text)
  st_filtered = State(f'There are {len(accountList)} matches')
  for acc in accountList:
    st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
  return st_filtered

# returns next state containing list of accounts filtered by email
def fog_getAccountsWithEmail(email):
  def outputfunc():
    accountList = master.filterAccountsByEmail(email)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
    return st_filtered
  return outputfunc

# function object that shows all emails used in accounts
def fo_getEmailList():
  st_emailList = State('Emails:')
  for email in master.emailList:
    st_emailList.addOption(Option(email, fog_getAccountsWithEmail(email), textInput=False))
  return st_emailList


# returns next state containing list of accounts filtered by username
def fog_getAccountsWithUsername(username):
  def outputfunc():
    accountList = master.filterAccountsByUsername(username)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
    return st_filtered
  return outputfunc

# function object that shows all usernames used in accounts
def fo_getUsernameList():
  st_usernameList = State('Usernames:')
  for i in master.usernameList:
    st_usernameList.addOption(Option(i, fog_getAccountsWithUsername(i), textInput=False))
  return st_usernameList

# returns next state containing list of accounts filtered by password
def fog_getAccountsWithPassword(password):
  def outputfunc():
    accountList = master.filterAccountsByPassword(password)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
    return st_filtered
  return outputfunc

# function object that shows all passwords used in accounts
def fo_getPasswordList():
  st_passwordList = State('Passwords:')
  for i in master.passwordList:
    st_passwordList.addOption(Option(i, fog_getAccountsWithPassword(i), textInput=False))
  return st_passwordList


# returns next state containing list of accounts filtered by name of linked account
def fog_getAccountsWithLinkedAccount(name):
  def outputfunc():
    accountList = master.filterAccountsByLinkedAccount(name)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.name, fog_focusAccount(acc), textInput=False))
    return st_filtered
  return outputfunc

# function object that shows all linked accounts used in accounts
def fo_getLinkedAccountList():
  st_linkedAccountList = State('Linked Accounts:')
  for i in master.linkedAccountList:
    st_linkedAccountList.addOption(Option(i, fog_getAccountsWithLinkedAccount(i), textInput=False))
  return st_linkedAccountList



# returns function object that calls data functions to change 
# the selected field of given account
def fog_editName(account):
  def outputfunc(text):
    updatedAccount = master.editName(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc
def fog_editEmail(account):
  def outputfunc(text):
    updatedAccount = master.editEmail(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc
def fog_editUsername(account):
  def outputfunc(text):
    updatedAccount = master.editUsername(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc
def fog_editPassword(account):
  def outputfunc(text):
    updatedAccount = master.editPassword(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc
def fog_editLinkedAccount(account):
  def outputfunc(text):
    updatedAccount = master.editLinkedAccount(account, text)
    manager.popStack(2)
    return fog_focusAccount(updatedAccount)()
  return outputfunc

def stringifyAccount(account):
  return \
    f'Account   : {account.name}\n'+ \
    f'username  : {account.username}\n' + \
    f'email     : {account.email}\n' + \
    f'password  : {account.password}\n' + \
    f'linked Acc: {account.linkedAccount}\n'

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
    st_editLinkeAccounts = State(f'Old account linked: {account.linkedAccount}')
    st_editLinkeAccounts.addOption(Option("New account linked: ", fog_editLinkedAccount(account)))

    st_viewAccount.addOption(Option('Edit Name', fog_nextState(st_editName)))
    st_viewAccount.addOption(Option('Edit Username', fog_nextState(st_editUsername)))
    st_viewAccount.addOption(Option('Edit Email', fog_nextState(st_editEmail)))
    st_viewAccount.addOption(Option('Edit Password', fog_nextState(st_editPassword)))
    st_viewAccount.addOption(Option('Edit LinkedAccounts', fog_nextState(st_editLinkeAccounts)))
    st_viewAccount.addOption(Option('Exit', fo_home))
    return st_viewAccount
  return outputfunc


### end of processes


if __name__ == '__main__':

  # Init Options and States
  print('Hashv2 running...')

  master = Master()
  master.load()

  manager = Manager()
  manager.initialization()
  manager.run()

  master.save()
