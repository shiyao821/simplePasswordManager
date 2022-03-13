# Simple Password Manager

Created to manage and track passwords and login information with total control and as few dependencies as possible


## Setup

Make sure you can run Python3 and have the latest `pip`.
```
pip install cryptography
```

I'm on windows and I like to set an alias for fast startup
```
pw=cd "C:\Users\somwhereOverTheRainbow" && python pwm.py
```

## Running

```
python pwm.py
```

A master password will be set on first startup (in the case where the `accounts.data` file is not found). Remember it well.

Input will either be options based, which will require the user to enter `1`, `2`, `3` etc, or text based.

For ease of access, during option-based scenarios, the following keys mapped to the respective numbers:
```
'q': '4',
'w': '5',
'e': '6',
'a': '7',
's': '8',
'd': '9'
```
The operation of the manager is based on states. You can jump back to the previous state with a backtick `` ` `` input. You can also exit the program with a double backtick input ` `` `.

## Note

Always backup the `accounts.data` file. At this moment I can't guarantee that it won't be corrupted during operation, though so far everything seems good.