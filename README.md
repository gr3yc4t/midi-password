# ♪ Midi Password Generator ♪
> The script uses a key derivation function to extract a cryptographic key from an array of MIDI notes, fetched in real-time.

### Dependencies
The script uses the <a href="https://pypi.org/project/python-rtmidi/">python-rtmidi</a> library that requires (on Linux) the following libraries
* build-essential
* libasound2-dev (For ALSA support)
* libjack-jackd2-dev (For Jack support)

To install them execute
```
sudo apt-get install build-essential
sudo apt-get install libasound2-dev #Just for ALSA
sudo apt-get install libjack-jackd2-dev #Just for Jack
```
After that you need to install the following python dependencies
* <a href="https://pypi.org/project/rtmidi-python/">rtmidi-python</a>
* <a href="https://pypi.org/project/hashlib/">hashlib</a>
* <a href="https://pypi.org/project/progress/">progress</a>
* <a href="https://pypi.org/project/argparse/">argparse</a>
```
sudo pip install hashlib progress argparse python-rtmidi 
```

Tested only on Ubuntu 18.04, for other OS support read the <a href="https://spotlightkid.github.io/python-rtmidi/installation.html">rtmidi installation page</a>

### Usage
Batch parameter
```
usage: main.py [-h] [-p PORT] [-m MIN_NOTE] [-s SALT] [-f FUNC] [-r ROUND]

Generate password through MIDI

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Midi port
  -m MIN_NOTE, --min-note MIN_NOTE
                        Minimun notes to play
  -s SALT, --salt SALT  Salt used in the key derivation function
  -f FUNC, --func FUNC  Key derivation function. Possible values : "pbkdf2",
                        "scrypt"
  -r ROUND, --round ROUND
                        Round to use in the key derivation function (Only in
                        pbkdf2 mode)
```
In case no argument is passed, the script asks for input interactively.
### How does it work
The script simply fetches MIDI events in real time, and store every note ("note on" event in particular) in a buffer, that in the end is passed through the <a href="https://en.wikipedia.org/wiki/PBKDF2">PBKDF2</a> key derivation function along with a used defined salt.  
