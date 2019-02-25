import rtmidi
import hashlib
import threading
import time
import binascii
from progress.bar import Bar, ChargingBar
import sys
import argparse
from blessings import Terminal
import math

#
#   Class that intercept MIDI note and store inside the provided buffer
#
class NoteFetcher(threading.Thread):

    #
    #   Param: 
    #   - midiIn = The rtmidi interface
    #   - buffer = Buffer where store notes
    #   - midiTimeout = (Optional) The minimum interval of time between two notes to be correctly fetched
    #
    def __init__(self, midiIn, buffer, midiTimeout=250):
        self.buffer = buffer
        self._stopevent = threading.Event()
        self.midiIn = midiIn
        self.midiTimeout = midiTimeout

        threading.Thread.__init__(self)

    def run(self):

        while not self._stopevent.isSet():

            m = self.midiIn.getMessage(self.midiTimeout) # some timeout in ms
            if m:
                self.parseNote(m)   
        print("Thread stopped")

        return

    def join(self):
        #Stop the Thread
        self._stopevent.set()
        threading.Thread.join(self)

    def print_message(self, midi):
        if midi.isNoteOn():
            print('ON: ', midi.getMidiNoteName(midi.getNoteNumber()), midi.getVelocity())
        elif midi.isNoteOff():
            print('OFF:', midi.getMidiNoteName(midi.getNoteNumber()))
        elif midi.isController():
            print('CONTROLLER', midi.getControllerNumber(), midi.getControllerValue())

    def parseNote(self, note):
        if note.isNoteOn():
            self.buffer.append(note)


    def extractByte(self):
        byte_buffer = bytearray()
        for note in self.buffer:
            byte = note.getNoteNumber()
            byte_buffer.append(byte)
        return byte_buffer


def getPortNumber(port_num, devices, term):
    print("Port Listing")
    for i in range(port_num):
        print("\t -" + term.yellow + "(" + term.normal + term.bold + str(i) + term.normal + term.yellow + ") " + term.normal + devices[i])
    print("\t -" + term.yellow + "(" + term.normal + term.bold + "99" + term.normal + term.yellow + ")" + term.normal + " Refresh devices")

    while True:
        port = int(input("Select Port: "))
        if port == 99:
            return "REFRESH"    
        elif port > port_num or port < 0:
            print("[X] Please select a valid port\n")
            continue
        break
    
    return port


def fetchParameter(*args):
    parser = argparse.ArgumentParser(description='Generate password through MIDI')
    parser.add_argument('-p', '--port', help='Midi port', required=False, type=int)
    parser.add_argument('-m', '--min-note', help='Minimun notes to play', required=False, type=int)
    parser.add_argument('-s', '--salt', help='Salt used in the key derivation function', required=False, type=str)
    
    parser.add_argument('-f', '--func', help='Key derivation function. Possible values :\n\t "pbkdf2", "scrypt"', required=False, type=str)
    parser.add_argument('-r', '--round', help='Round to use in the key derivation function (Only in pbkdf2 mode)', required=False, type=int, default=200000)

    args = parser.parse_args()

    return vars(args)


def sigint_handler(signum, frame):
    print 'Stop pressing the CTRL+C!'

def blockEntropy(A,m):N=len(A)-m+1;R=range(N);return sum(math.log(float(N)/b) for b in [sum(A[i:i+m]==A[j:j+m] for i in R) for j in R])/N

def main(*args):

    param = fetchParameter(*args)
    t = Terminal()

    if param['min_note'] != None:
        min_notes = param['min_note']
    else:
        min_notes = 40

    midiIn = rtmidi.RtMidiIn()

    port_num = midiIn.getPortCount()
    ports = range(port_num)

    if not ports:
        print("No open port found, exiting...")
        exit()

    if param['port'] != None:
        print("Using port " + t.bold + str(param['port']) + t.normal)
        port = param['port']

        if port > port_num or port < 0:
            print("\n" + t.bold + t.red + "[X]"  + t.normal + "Invalid port selected\n")
            exit()

    else:
        #Start the getPortNumber routine
        while True:
            devices = {}
            
            port_num = midiIn.getPortCount()
            ports = range(port_num)
            
            for i in ports:
                devices[i] = str(midiIn.getPortName(i))

            port = getPortNumber(port_num, devices, t)

            if port != "REFRESH":
                break



    print("\nOpening port: " + t.bold + str(port) + t.normal)
    
    midiIn.openPort(port)


    buffer = []

    fetcher = NoteFetcher(midiIn, buffer)
    fetcher.start()     #Start the fetcher in another thread

    print t.underline + "Continue to play notes until the entropy bar is full\n" + t.no_underline

    bar = ChargingBar('Entropy', suffix='%(percent)d%%', max=min_notes)
    prev_dim = 0


    while len(buffer) < min_notes:
        if len(buffer) != prev_dim:
            for i in range(len(buffer)-prev_dim):
                bar.next()
            prev_dim = len(buffer)
        time.sleep(0.01)


    bar.finish()

    cmd = ""
    while cmd != "stop":
        cmd = str(raw_input("\nWrite \"" + t.bold + t.red + "stop" + t.normal + "\" to generate the password: "))

    fetcher.join()  #Stop the fetcher thread

    time.sleep(0.2)

    byte_buffer = fetcher.extractByte()

    print("\n" + t.underline + "Final array" + t.no_underline + ": " + binascii.hexlify(byte_buffer))

    note_list = ""
    for note in buffer:
        note_list += note.getMidiNoteName(note.getNoteNumber()) + " "
    print("\nNotes:\n\t" + note_list)


    print("\n\n")

    #Set the Salt
    if param['salt'] != None:
        salt = param['salt']
    else:
        salt = str(raw_input("Insert a salt: "))

    #Select the key derivation function
    if param['func'] == None:
        while True:
            print("\nSelect the algorithm to use for the key derivation")
            print("\n\t" + t.yellow + "(" + t.normal + t.bold + "0" + t.normal + t.yellow + ")" + t.normal + " - pbkdf2 (default)\n\t" + t.yellow + "(" + t.normal + t.bold + "1" + t.normal + t.yellow + ")" + t.normal + "- scrypt (unimplemented)")
            key_func = int(raw_input("Choice : "))
            if key_func == 0:
                param['func'] = "pbkdf2"
                break
            elif key_func == 1:
                #param['func'] = "scrypt"
                #break
                print("Unimplemented :-(\n")
            else:
                print("Please choose a valid function\n")
                continue


    if param['func'] == "pbkdf2":
        key = hashlib.pbkdf2_hmac('sha512', byte_buffer, salt, param['round'])
    elif param['func'] == "scrypt":
        #n = int(raw_input("Insert 'n' parameter: "))
        #r = int(raw_input("Insert 'r' parameter: "))
        #p = int(raw_input("Insert 'p' parameter: "))
        #key_len = int(raw_input("Insert key length: "))
        #key = hashlib.scrypt(buffer, salt, n, r, p, dklen=key_len)
        print("Unimplemented")

    hex_key = binascii.hexlify(key)

    print("\n\nKey is : \t| " + t.bold + str(hex_key) + t.normal + " |\n\n")





if __name__ == '__main__':
    main(*sys.argv[1:])