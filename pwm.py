from getpass import getpass
from types import FunctionType, MethodType
from pwmdata import Database, Account, EmptyInputException
from cryptography.fernet import InvalidToken

### High level view:
# States are used to facilitate going 'back' to the previous step. User input = '`'
# Manager navigates between states using a stack
#
# States can be:
#   1) option-choosing states
#      - if > 1 option: user enters 1/2/3... to select
#      - if exactly 1 option: fast-forwarded without needing user input
#   2) text-input states
#      - exactly 1 option with option.textInput=True; user enters free text
#      - if option.passwordInput=True, getpass() is used to hide the input
#
# Options contain:
#   1) a display message string
#   2) a function object that executes when the option is chosen
#
# Naming conventions:
#   fo_  methods are function objects (used directly as callbacks)
#   fog_ methods are function object generators (return a callback)


class Manager:

    MAX_COL_WIDTH = 28
    TOTAL_COLUMNS = 4
    INDENT = 2
    MISC_TITLE_MIN_WIDTH = 9

    def __init__(self, data: Database) -> None:
        self.stateStack = []
        self.data = data

    def viewStack(self):
        return self.stateStack[-1]

    def pushStack(self, state):
        self.stateStack.append(state)

    def popStack(self, num=1):
        del self.stateStack[-num:]

    def popStackUntil(self, leftover):
        del self.stateStack[leftover:]

    def fo_home(self):
        self.popStackUntil(1)

    def run(self):
        while self.stateStack:
            self.readStack()

    def readStack(self):
        currentState = self.viewStack()
        print(f'\n{currentState.displayMessage}')
        options = currentState.options

        if not options:
            self.popStack()
            return

        if len(options) == 1:
            option = options[0]
            try:
                if option.textInput:
                    prompt_fn = getpass if option.passwordInput else input
                    text = prompt_fn(f'{option.message}')
                    if text == '`':
                        printn('"Back" registered')
                        self.popStack()
                        return
                    if text == '``':
                        printn('"Exit" registered')
                        self.popStackUntil(0)
                        return
                    option.execute(text)
                else:
                    # Single non-text option: fast-forward, pop for clean back-navigation
                    self.popStack()
                    option.execute()
            except EmptyInputException:
                print("Nothing was entered")
                self.popStack()
            return

        # Multiple options: numbered selection
        for n, option in enumerate(options):
            label = str(n + 1)
            truncated = option.message[:self.MAX_COL_WIDTH - self.INDENT - len(label) - 1]
            padding = max(self.MAX_COL_WIDTH - self.INDENT - len(label) - len(truncated) + 1, 1)
            print(f'{label}. {truncated}' + ' ' * padding, end='')
            if n % self.TOTAL_COLUMNS == self.TOTAL_COLUMNS - 1:
                print()
        print()

        text = input('(1/2/3/...) >>> ')
        # Keyboard shortcuts for easy reach on QWERTY
        text = {'q': '4', 'w': '5', 'e': '6', 'a': '7', 's': '8', 'd': '9'}.get(text, text)

        if text.isdigit():
            choice = int(text) - 1
            try:
                options[choice].execute()
            except IndexError:
                print('Not within options given')
        elif text == '`':
            printn('"Back" registered')
            self.popStack()
        elif text == '``':
            printn('"Exit" registered')
            self.popStackUntil(0)
        else:
            print(f'Invalid input: {text}')

    # --- Initialization ---

    def initialization(self):
        st_home = State('Yo sup')
        self.pushStack(st_home)

        st_addAccount = State('Adding new account')
        st_addAccount.addOption(Option('Account name: ', self.fo_addAccount))

        st_searchByName = State('Search by Account Name')
        st_searchByName.addOption(Option('Enter keyword to search: ', self.fo_searchByAccountName))

        st_checkMasterPassword = State('Changing Master Password\nYou can backtrack with "`"')
        st_checkMasterPassword.addOption(Option('Enter current master password: ', self.fo_checkMasterPassword, passwordInput=True))

        st_home.addOption(Option('Search by Name',          self.fog_nextState(st_searchByName)))
        st_home.addOption(Option('Add New Account',         self.fog_nextState(st_addAccount)))
        st_home.addOption(Option('Search by Email',         self.fo_getEmailList))
        st_home.addOption(Option('Search by Username',      self.fo_getUsernameList))
        st_home.addOption(Option('Search by Password',      self.fo_getPasswordList))
        st_home.addOption(Option('Search by Phone Number',  self.fo_getPhoneList))
        st_home.addOption(Option('Search by Linked Account', self.fo_getLinkedAccountsList))
        st_home.addOption(Option('Change Master Password',  self.fog_nextState(st_checkMasterPassword)))

        try:
            password = getpass("Please enter your password: ")
            self.data.load(password)
        except InvalidToken:
            print('The password you have entered is invalid')
            self.popStackUntil(0)
        except FileNotFoundError:
            print(
                f'Data file "{self.data.DATA_FILE_NAME}" does not exist.\n'
                'It seems like this is your first time using the program.'
            )
            self.data.masterPassword = input("Please set up a password: ")

    # --- Master password management ---

    def fo_checkMasterPassword(self, text):
        if self.data.masterPassword == text:
            st_enterNewPass = State('Authentication complete')
            st_enterNewPass.addOption(Option('Enter new master password: ', self.fo_enterNewMasterPassword, passwordInput=True))
            self.pushStack(st_enterNewPass)
        else:
            print('Incorrect password')

    def fo_enterNewMasterPassword(self, newPassword):
        if not newPassword:
            print('New password must not be empty')
            self.fo_home()
            return
        st_confirm = State('Confirm the new password')
        st_confirm.addOption(Option('Re-enter new master password: ', self.fog_confirmNewMasterPassword(newPassword), passwordInput=True))
        self.pushStack(st_confirm)

    def fog_confirmNewMasterPassword(self, password):
        def handler(text):
            if text == password:
                self.data.updateMasterPassword(password)
                print('Master password updated')
            else:
                print('Passwords do not match')
            self.fo_home()
        return handler

    # --- Account search / filtering ---

    def fo_searchByAccountName(self, text):
        self._push_account_list_state(self.data.filterAccountsByAccountName(text))

    def fo_getEmailList(self):
        self._push_filtered_by_field('Emails:', self.data.emailList, self.data.filterAccountsByEmail)

    def fo_getUsernameList(self):
        self._push_filtered_by_field('Usernames:', self.data.usernameList, self.data.filterAccountsByUsername)

    def fo_getPasswordList(self):
        self._push_filtered_by_field('Passwords:', self.data.passwordList, self.data.filterAccountsByPassword)

    def fo_getPhoneList(self):
        self._push_filtered_by_field('Phone Numbers:', self.data.phoneList, self.data.filterAccountsByPhone)

    def fo_getLinkedAccountsList(self):
        self._push_filtered_by_field('Linked Accounts:', self.data.linkedAccountsList, self.data.filterAccountsByLinkedAccounts)

    def _push_account_list_state(self, accounts):
        """Push a state listing the given accounts as selectable options."""
        st = State(f'There are {len(accounts)} matches')
        for acc in accounts:
            st.addOption(Option(acc.accountName, self.fog_focusAccount(acc), textInput=False))
        self.pushStack(st)

    def _push_filtered_by_field(self, title, items, filter_func):
        """Push a state listing items; selecting one shows accounts matching that item."""
        st = State(title)
        for item in items:
            def make_handler(val):
                def handler():
                    self._push_account_list_state(filter_func(val))
                return handler
            st.addOption(Option(item, make_handler(item), textInput=False))
        self.pushStack(st)

    # --- Account view & editing ---

    def fog_focusAccount(self, account):
        def outputfunc():
            st_view = State(f'{self.stringifyAccount(account)}\n\nWhat do?')

            st_editName     = State(f'Old account name: {account.accountName}')
            st_editUsername = State(f'Old username: {account.username}')
            st_editEmail    = State(f'Old email: {account.email}')
            st_editPassword = State(f'Old password: {account.password}')
            st_editPhone    = State(f'Old phone number: {account.phone}')
            st_editLinked   = State(f'Currently linked accounts: {account.linkedAccounts}')
            st_editMisc     = State('What field to edit / delete? (adds field if it does not exist)')

            st_editName.addOption(Option('New account name: ',       self._make_field_editor(account, self.data.editAccountName)))
            st_editUsername.addOption(Option('New username: ',       self._make_field_editor(account, self.data.editUsername)))
            st_editEmail.addOption(Option('New email: ',             self._make_field_editor(account, self.data.editEmail)))
            st_editPassword.addOption(Option('New password: ',       self._make_field_editor(account, self.data.editPassword)))
            st_editPhone.addOption(Option('New phone number: ',      self._make_field_editor(account, self.data.editPhone)))
            st_editLinked.addOption(Option('Account to add/remove: ', self._make_field_editor(account, self.data.editLinkedAccounts)))
            st_editMisc.addOption(Option('Field name: ',             self.fog_chooseField(account)))

            st_deleteConfirm = State(f'Are you sure you want to delete "{account.accountName}"?')
            st_deleteConfirm.addOption(Option('Enter 1 to confirm, anything else to cancel: ', self.fog_deleteAccount(account)))

            st_view.addOption(Option('Edit Account Name',    self.fog_nextState(st_editName)))
            st_view.addOption(Option('Edit Username',        self.fog_nextState(st_editUsername)))
            st_view.addOption(Option('Edit Email',           self.fog_nextState(st_editEmail)))
            st_view.addOption(Option('Edit Password',        self.fog_nextState(st_editPassword)))
            st_view.addOption(Option('Edit Phone Number',    self.fog_nextState(st_editPhone)))
            st_view.addOption(Option('Edit Linked Accounts', self.fog_nextState(st_editLinked)))
            st_view.addOption(Option('Edit Misc Info',       self.fog_nextState(st_editMisc)))
            st_view.addOption(Option('Delete Account',       self.fog_nextState(st_deleteConfirm)))
            st_view.addOption(Option('Exit',                 self.fo_home))
            self.pushStack(st_view)
        return outputfunc

    def _make_field_editor(self, account, edit_func):
        """Return a callback that calls edit_func, then re-focuses the updated account."""
        def handler(text):
            updated = edit_func(account, text)
            self.popStack(2)
            self.fog_focusAccount(updated)()
        return handler

    def fo_addAccount(self, text):
        if self.data.checkAccountNameExists(text):
            print(f'Account with name "{text}" already exists')
            return
        new_acc = Account(accountName=text)
        added_acc = self.data.addAccount(new_acc)
        self.popStack(1)
        self.fog_focusAccount(added_acc)()

    def fog_deleteAccount(self, acc):
        def handler(confirmation):
            if confirmation == '1':
                self.data.deleteAccount(acc)
                self.fo_home()
        return handler

    def fog_chooseField(self, acc):
        def handler(field):
            if field in acc.misc:
                st = State(f'Old value: {acc.misc[field]}')
                st.addOption(Option('New value: ', self.fog_editField(acc, field)))
            else:
                st = State(f'Adding new field: {field}')
                st.addOption(Option('Value: ', self.fog_editField(acc, field)))
            self.pushStack(st)
        return handler

    def fog_editField(self, acc, field):
        def handler(value):
            updated = self.data.editMiscField(acc, field, value)
            self.popStack(3)
            self.fog_focusAccount(updated)()
        return handler

    def fog_nextState(self, next_state):
        def handler():
            self.pushStack(next_state)
        return handler

    # --- String formatting ---

    def stringifyAccount(self, account: Account) -> str:
        return (
            f'Account    : {account.accountName}\n'
            f'last edited: {account.lastEdited.isoformat(sep=" ", timespec="seconds")}\n'
            f'username   : {account.username}\n'
            f'email      : {account.email}\n'
            f'password   : {account.password}\n'
            f'phone      : {account.phone}\n'
            f'linked Acc : {", ".join(account.linkedAccounts)}\n'
            f'misc       :\n'
            f'{self.stringifyMisc(account.misc)}'
        )

    def stringifyMisc(self, misc: dict) -> str:
        lines = []
        for key, value in misc.items():
            parts = value.split('\n')
            padding = ' ' * max(self.MISC_TITLE_MIN_WIDTH - len(key), 0)
            lines.append(f'  {key}{padding}: {parts[0]}')
            for part in parts[1:]:
                lines.append(f'  {" " * self.MISC_TITLE_MIN_WIDTH}  {part}')
        return '\n'.join(lines) + ('\n' if lines else '')


class State:
    def __init__(self, displayMessage: str) -> None:
        self.displayMessage = displayMessage
        self.options: list['Option'] = []

    def addOption(self, option: 'Option'):
        self.options.append(option)


class Option:
    def __init__(self, message: str, functionObj, textInput=True, passwordInput=False) -> None:
        if not isinstance(functionObj, (MethodType, FunctionType)):
            raise TypeError("Option: functionObj must be a function or method")
        self.message = message
        self.functionObj = functionObj
        self.textInput = textInput
        self.passwordInput = passwordInput

    def execute(self, *args):
        return self.functionObj(*args) if args else self.functionObj()


def printn(text):
    """Print with a preceding newline."""
    print(f'\n{text}')


if __name__ == '__main__':
    print('Password Manager running...')
    data = Database()
    manager = Manager(data)
    manager.initialization()
    manager.run()
    print("Exiting Password Manager")
