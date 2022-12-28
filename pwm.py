from getpass import getpass
from types import FunctionType, MethodType
from pwmdata import Database, Account, EmptyInputException
from cryptography.fernet import InvalidToken

### High level view:
# States are used to facilitate going 'back' to the previous step. User input = '`'
# Manager navigates between states using a stack
### States can be: 
# 1) option-choosing states 
# - if it has > 1 option in the options list to display, user enters 1/2/3/4 etc
# - if it has exactly 1 option. That option will be executed immediately (fast-forwarded) without needing user input. 
# or 2) text-input states
# - definitely only 1 option in the list, with option.textInput=True, user enters text input
# - if option.passwordInput=True, the getpass function will be used to hide password inputs
# a state may be dynamically generated with additional dynamic data
### Options will contain:
# 1) message string
# 2) function object that can be called to execute
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
  MISC_TITLE_MIN_CHAR_DISPLAYED = 8

  def __init__(self, data) -> None:
    self.stateStack = []
    self.data = data

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
    currentState = self.viewStack()
    print(f'\n{currentState.displayMessage}')
    optionsLength = len(currentState.options)
    if optionsLength == 0:
      self.popStack()
      return
    # 1 Option: check if text input state. Otherwise, fast forward to option function
    elif optionsLength == 1:
      try:
        option = currentState.options[0]
        if option.textInput:
          if option.passwordInput:
            text = getpass(f'{option.message}')
          else:
            text = input(f'{option.message}')
          if text == '`':
            printn('"Back" registered')
            self.popStack()
            return
          if text == '``':
            printn('"Exit" registered')
            self.popStackUntil(0)
            return
          option.execute(text)
        # 1 Option, but not for text input -> fast forward to selection
        # pop stack for double jump back
        else:
          self.popStack()
          option.execute()
      except EmptyInputException:
        print("Nothing was entered")
        self.popStack()
    # Choice input states
    else:
      for n, option in enumerate(currentState.options):
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
          currentState.options[choice].execute()
        except IndexError:
          print('Not within options given')
      elif text == '`':
        printn('"Back" registered')
        self.popStack()
        return
      elif text == '``':
        printn('"Exit" registered')
        self.popStackUntil(0)
        return
      else:
        print(f'Invalid input: {text}')

  # removes all stacks until a number of leftovers
  def popStackUntil(self, leftover):
    while len(self.stateStack) > leftover:
      self.popStack()

  # function object that returns manager to home state
  def fo_home(self):
    self.popStackUntil(1)

  def run(self):
    while len(self.stateStack) > 0:
      self.readStack()

  # creating the state tree from root to branches
  def initialization(self):
    # Home state:
    st_home = State('Yo sup')
    self.pushStack(st_home)

    st_addAccount = State('Adding new account')
    st_addAccount.addOption(Option('Account name: ', self.fo_addAccount))
    st_deleteAccount = State('Deleting account')
    st_searchByAccountName = State('Search by Account Name')
    st_checkMasterPassword = State('Changing Master Password\nYou can backtrack this process with "`"')
    st_checkMasterPassword.addOption(Option('Enter current master password: ', self.fo_checkMasterPassword, passwordInput=True))
    
    st_home.addOption(Option('Search by Name', self.fog_nextState(st_searchByAccountName)))
    st_home.addOption(Option('Add New Account', self.fog_nextState(st_addAccount)))
    st_home.addOption(Option('Search by Email', self.fo_getEmailList))
    st_home.addOption(Option('Search by Username', self.fo_getUsernameList))
    st_home.addOption(Option('Search by Password', self.fo_getPasswordList))
    st_home.addOption(Option('Search by Phone Number', self.fo_getPhoneList))
    st_home.addOption(Option('Search by Linked Account', self.fo_getlinkedAccountsList))
    st_home.addOption(Option('Change Master Password', self.fog_nextState(st_checkMasterPassword)))
    # st_home.addOption(Option('Delete Account Entry', self.fog_nextState(st_deleteAccount))) TODO

    opt_inputKeyword = Option('Enter keyword to search:', self.fo_searchByAccountName)
    st_searchByAccountName.addOption(opt_inputKeyword)

    try:
      password = getpass("Please enter your password: ")
      self.data.load(password)
    except InvalidToken:
      print('The password you have entered is invalid')
      self.popStackUntil(0)
    except FileNotFoundError:
      print(f'Data file {self.data.DATA_FILE_NAME} does not exist. \n' + \
        'It seems like this is your first time using the program.')
      self.masterPassword = input("Please setup a password: ")


  # function object that checks current master password for authentication
  def fo_checkMasterPassword(self, text):
    if data.masterPassword == text:
      st_enterNewPass = State('Authentication Complete')
      st_enterNewPass.addOption(Option('Enter new master password: ', self.fo_enterNewMasterPassword, passwordInput=True))
      self.pushStack(st_enterNewPass)
    else:
      print('The password you have entered is invalid')

  def fo_enterNewMasterPassword(self, newPassword):
    if len(newPassword) == 0:
      print('New password must not be empty')
      self.fo_home()
      return
    st_confirmNewPass = State('Confirm the new password')
    st_confirmNewPass.addOption(Option('Re-enter new master password', self.fog_confirmNewMasterPassword(newPassword), passwordInput=True))
    self.pushStack(st_confirmNewPass)

  # function object generator that asks for password again for confirmation
  def fog_confirmNewMasterPassword(self, password):
    def outputfunc(text):    
      if text == password:
        data.updateMasterPassword(password)
        print('Master password updated')
      else:
        print('password entered does not match')
      # back to home state regardless of match
      self.fo_home()
    return outputfunc

  # function object that requests for keyword input to filter data data
  # returns next state containing list of accounts filtered
  def fo_searchByAccountName(self, text):
    accountList = data.filterAccountsByAccountName(text)
    st_filtered = State(f'There are {len(accountList)} matches')
    for acc in accountList:
      st_filtered.addOption(Option(acc.accountName, self.fog_focusAccount(acc), textInput=False))
    self.pushStack(st_filtered)

  # returns next state containing list of accounts filtered by email
  def fog_getAccountsWithEmail(self, email):
    def outputfunc():
      accountList = data.filterAccountsByEmail(email)
      st_filtered = State(f'There are {len(accountList)} matches')
      for acc in accountList:
        st_filtered.addOption(Option(acc.accountName, self.fog_focusAccount(acc), textInput=False))
      self.pushStack(st_filtered)
    return outputfunc

  # function object that shows all emails used in accounts
  def fo_getEmailList(self):
    st_emailList = State('Emails:')
    for email in data.emailList:
      st_emailList.addOption(Option(email, self.fog_getAccountsWithEmail(email), textInput=False))
    self.pushStack(st_emailList)

  # returns next state containing list of accounts filtered by username
  def fog_getAccountsWithUsername(self, username):
    def outputfunc():
      accountList = data.filterAccountsByUsername(username)
      st_filtered = State(f'There are {len(accountList)} matches')
      for acc in accountList:
        st_filtered.addOption(Option(acc.accountName, self.fog_focusAccount(acc), textInput=False))
      self.pushStack(st_filtered)
    return outputfunc

  # function object that shows all usernames used in accounts
  def fo_getUsernameList(self):
    st_usernameList = State('Usernames:')
    for i in data.usernameList:
      st_usernameList.addOption(Option(i, self.fog_getAccountsWithUsername(i), textInput=False))
    self.pushStack(st_usernameList)

  # returns next state containing list of accounts filtered by password
  def fog_getAccountsWithPassword(self, password):
    def outputfunc():
      accountList = data.filterAccountsByPassword(password)
      st_filtered = State(f'There are {len(accountList)} matches')
      for acc in accountList:
        st_filtered.addOption(Option(acc.accountName, self.fog_focusAccount(acc), textInput=False))
      self.pushStack(st_filtered)
    return outputfunc

  # function object that shows all passwords used in accounts
  def fo_getPasswordList(self):
    st_passwordList = State('Passwords:')
    for i in data.passwordList:
      st_passwordList.addOption(Option(i, self.fog_getAccountsWithPassword(i), textInput=False))
    self.pushStack(st_passwordList)
    
  # returns next state containing list of accounts filtered by phone number
  def fog_getAccountsWithPhone(self, phone):
    def outputfunc():
      accountList = data.filterAccountsByPhone(phone)
      st_filtered = State(f'There are {len(accountList)} matches')
      for acc in accountList:
        st_filtered.addOption(Option(acc.accountName, self.fog_focusAccount(acc), textInput=False))
      self.pushStack(st_filtered)
    return outputfunc

  # function object that shows all passwords used in accounts
  def fo_getPhoneList(self):
    st_phoneList = State('Phone Numbers:')
    for i in data.phoneList:
      st_phoneList.addOption(Option(i, self.fog_getAccountsWithPhone(i), textInput=False))
    self.pushStack(st_phoneList)

  # returns next state containing list of accounts filtered by accountName of linked account
  def fog_getAccountsWithLinkedAccount(self, accountName):
    def outputfunc():
      accountList = data.filterAccountsByLinkedAccounts(accountName)
      st_filtered = State(f'There are {len(accountList)} matches')
      for acc in accountList:
        st_filtered.addOption(Option(acc.accountName, self.fog_focusAccount(acc), textInput=False))
      self.pushStack(st_filtered)
    return outputfunc

  # function object that shows all linked accounts used in accounts
  def fo_getlinkedAccountsList(self):
    st_linkedAccountsList = State('Linked Accounts:')
    for i in data.linkedAccountsList:
      st_linkedAccountsList.addOption(Option(i, self.fog_getAccountsWithLinkedAccount(i), textInput=False))
    self.pushStack(st_linkedAccountsList)

  # returns function object that calls data functions to change 
  # the selected field of given account
  def fog_editAccountName(self, account):
    def outputfunc(text):
      updatedAccount = data.editAccountName(account, text)
      self.popStack(2)
      return self.fog_focusAccount(updatedAccount)()
    return outputfunc
  def fog_editEmail(self, account):
    def outputfunc(text):
      updatedAccount = data.editEmail(account, text)
      self.popStack(2)
      return self.fog_focusAccount(updatedAccount)()
    return outputfunc
  def fog_editUsername(self, account):
    def outputfunc(text):
      updatedAccount = data.editUsername(account, text)
      self.popStack(2)
      return self.fog_focusAccount(updatedAccount)()
    return outputfunc
  def fog_editPassword(self, account):
    def outputfunc(text):
      updatedAccount = data.editPassword(account, text)
      self.popStack(2)
      return self.fog_focusAccount(updatedAccount)()
    return outputfunc
  def fog_editPhone(self, account):
    def outputfunc(text):
      updatedAccount = data.editPhone(account, text)
      self.popStack(2)
      return self.fog_focusAccount(updatedAccount)()
    return outputfunc
  def fog_editLinkedAccounts(self, account):
    def outputfunc(text):
      updatedAccount = data.editLinkedAccounts(account, text)
      self.popStack(2)
      return self.fog_focusAccount(updatedAccount)()
    return outputfunc

  def stringifyAccount(self, account):
    return \
      f'Account   : {account.accountName}\n'+ \
      f'username  : {account.username}\n' + \
      f'email     : {account.email}\n' + \
      f'password  : {account.password}\n' + \
      f'phone     : {account.phone}\n' + \
      f'linked Acc: {self.stringifyLinkedAccounts(account.linkedAccounts)}\n' + \
      f'misc:\n' + \
      f'{self.stringifyMisc(account.misc)}'

  def stringifyLinkedAccounts(self, la):
    output = ''
    for a in la:
      output += a + ', '
    return output[:-2]

  # returns a string of the dict-type misc information variable to be printed
  def stringifyMisc(self, misc):
    # return str(misc)
    string = ''
    for item in misc.items():
      multiLine = item[1].split('\n')
      string += f'  {item[0]}{" " * max(self.MISC_TITLE_MIN_CHAR_DISPLAYED - len(item[0]), 0)}: {multiLine[0]}\n'
      for i in range(1, len(multiLine)):
        string += f'  {" " * self.MISC_TITLE_MIN_CHAR_DISPLAYED}  {multiLine[i]}\n'
    return string

  # returns function object that displays given account details, 
  # with next state that edits or exits
  def fog_focusAccount(self, account):
    def outputfunc():
      st_viewAccount = State(f'{self.stringifyAccount(account)}\n\nWhat do?')
      st_editAccountName = State(f'Old account name: {account.accountName}')
      st_editAccountName.addOption(Option("New account name: ", self.fog_editAccountName(account)))
      st_editUsername = State(f'Old account username: {account.username}')
      st_editUsername.addOption(Option("New account username: ", self.fog_editUsername(account)))
      st_editEmail = State(f'Old account email: {account.email}')
      st_editEmail.addOption(Option("New account email: ", self.fog_editEmail(account)))
      st_editPassword = State(f'Old account password: {account.password}')
      st_editPassword.addOption(Option("New account password: ", self.fog_editPassword(account)))
      st_editLinkeAccounts = State(f'Currently linked Accounts: {account.linkedAccounts}')
      st_editLinkeAccounts.addOption(Option("Type another account name to add, write an existing name to delete\n: ", self.fog_editLinkedAccounts(account)))
      st_editPhone = State(f'Old Phone number: {account.phone}')
      st_editPhone.addOption(Option("New Phone number: ", self.fog_editPhone(account)))
      st_editMisc = State(f'What field to edit / delete? (adds if not existent)')
      st_editMisc.addOption(Option('Field name: ', self.fog_chooseField(account)))

      st_deleteConfirmation = State(f'Are you sure you want to delete the account for {account.accountName}')
      st_deleteConfirmation.addOption(Option('1 = YES \\ enter = NO: ', self.fog_deleteAccount(account)))

      st_viewAccount.addOption(Option('Edit Account Name', self.fog_nextState(st_editAccountName)))
      st_viewAccount.addOption(Option('Edit Username', self.fog_nextState(st_editUsername)))
      st_viewAccount.addOption(Option('Edit Email', self.fog_nextState(st_editEmail)))
      st_viewAccount.addOption(Option('Edit Password', self.fog_nextState(st_editPassword)))
      st_viewAccount.addOption(Option('Edit Phone Number', self.fog_nextState(st_editPhone)))
      st_viewAccount.addOption(Option('Edit LinkedAccounts', self.fog_nextState(st_editLinkeAccounts)))
      st_viewAccount.addOption(Option('Edit Misc info', self.fog_nextState(st_editMisc)))
      st_viewAccount.addOption(Option('Delete Account', self.fog_nextState(st_deleteConfirmation)))
      st_viewAccount.addOption(Option('Exit', self.fo_home))
      self.pushStack(st_viewAccount)
    return outputfunc

  # function object that adds an account with input name to database,
  # returns with a state focusing on data. input name must not previously exist
  def fo_addAccount(self, text):
    if not data.checkAccountNameExists(text):
      acc = data.addAccount(Account(accountName=text))
      self.popStack(1)
      self.fog_focusAccount(acc)()
    else:
      print(f'Account with name "{text}" already exists')

  # returns a function object that takes 1 as input confirmation to delete selected acc
  def fog_deleteAccount(self, acc):
    def outputfunc(input):
      if input == '1':
        data.deleteAccount(acc)
        self.fo_home()
    return outputfunc

  # returns a function object that asks for field to edit
  # field exists: next state asks for new value, field doesn't exist: add key
  def fog_chooseField(self, acc):
    def outputfunc(field):
      if field in acc.misc:
        st_editField = State(f'Old value: {acc.misc[field]}')
        st_editField.addOption(Option('New value: ', self.fog_editField(acc, field)))
        self.pushStack(st_editField)
      else:
        st_addField = State(f'To add field: {field}')
        st_addField.addOption(Option('Value: ', self.fog_editField(acc, field)))
        self.pushStack(st_addField)
    return outputfunc

  # generates function object updates the misc field with requested value
  # if value is empty, field is deleted. Handled internally by data
  def fog_editField(self, acc, field):
    def outputfunc(value):
      updatedAcc = data.editMiscField(acc, field, value)
      self.popStack(3)
      self.fog_focusAccount(updatedAcc)()
    return outputfunc

  # returns a function object that returns the next state
  def fog_nextState(self, nextstate):
    def outputfunc():
      self.pushStack(nextstate)
    return outputfunc

class State:
  def __init__(self, displayMessage) -> None:
    self.displayMessage = displayMessage
    self.options = [] # initially empty

  def addOption(self, option):
    self.options.append(option)

class Option:
  def __init__(self, message, functionObj, textInput=True, passwordInput=False) -> None:
    if type(functionObj) != MethodType and type(functionObj) != FunctionType:
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

# wrapper to start a new print block on CLI
def printn(text):
  print(f'\n{text}')

### end of UTIL Functions

if __name__ == '__main__':

  # Init Options and States
  print('Password Manager running...')
  data = Database()
  manager = Manager(data)
  manager.initialization()
  manager.run()

  print("Exiting Password Manager")
