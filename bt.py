#!/usr/bin/python3
#this program aims to be a general purpos bluetooth swiss army knife
#much in the same way that nc aims to be a gerneral purpos tcp/ip tool
import bluetooth
from threading import Thread
import sys
import argparse
#this is the tread that will recive data and output it to the screen
class net_thread(Thread):
    def _init_(self):
        print('test')
    def run(self):
        #this is where we put the code that recvs info from the client
        data = self.arr[0].recv(self.size)
        while data:
            self.io[1].write(data)
            self.io[1].flush()
            data = self.arr[0].recv(self.size)
        self.arr[0].close()
    def set_client(self,arr,io,size):
        self.arr=arr
        self.io=io
        self.size=size

def bt_dns(name):
    #this is a simple function that takes a name as input and returns the bluetooth address nearest it
    #this needs to be hardened against more than one of the same name
    near_devices=bluetooth.discover_devices()
    for i in range(0,len(near_devices)):
        if name == bluetooth.lookup_name(near_devices[i]):
            return near_devices[i]
    #we were unable to find an address that corrisponds to the given name
    return None
def hex_check(digit):
    #this function checks a single digit against a white list of valid hex charicters
    key='0123456789ABCDEFabcdef'
    for i in range(0,len(key)):
        if digit == key[i]:
            return True
    return False
def parse_addr(addr):
    #this function returns none if the address is not valid and addr if the addr would work for bluetooth
    ret_addr = ''
    mac = False
    split = addr.split(':')
    if len(split) == 6:
        mac = True
        for i in range(0,len(split)):
            #check to make sure that all of the given inputs are valid hex
            if len(split[i]) != 2:
                mac = False
                break
            elif not (hex_check(split[i][0]) and hex_check(split[i][1])):
                mac = False
                break
    if mac == False:
        return None
    else:
        return addr
        #this returns None if it cannot find the name of the bluetooth address

def main():

    parser = argparse.ArgumentParser(description='A bluetooth swiss army knife')
    parser.add_argument('-l','--listen',action='store_true',help="Run as a misclanious bluetooth server")
    parser.add_argument('-c','--chat',action='store_true',help="Run in chat mode, read in on new line")
    parser.add_argument('-v','--verbos',action='store_true',help="output additional information to stderr")
    parser.add_argument('-s','--size',type=int,help='the size of data to read in before sending information over the network')
    parser.add_argument('-a','--addr',type=str,help="bluetooth address to connect to or listen on, must be specified when connecting")
    parser.add_argument('-p','--port',type=int,help="port to connect to or listen on",required=True)
    args=parser.parse_args()
    
    #opent the files required for i/o
    cout = open(1,'wb')
    cin = open(0,'rb')
    cerr = open(2,'wb')

    # we are going to need to do this no matter what else we do when the program is run, so open it gaurenteed
    sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )

    #these will need to be variable args from the library
    port = args.port
    #addr needs to be initilised as an empty string
    addr = ''
    size = 1024
    if args.size != None:
        size = args.size

    #are we running as the client?
    if args.listen == False:
        #did the they supply an address?
        if args.addr == None:
            #no
            cerr.write(b'ERROR: address required as client\n')
            quit()            
        #we have an address, check if its valid
        addr=parse_addr(args.addr)
        if addr == None:
            #its not a valid bluetooth address, either its a name or invalid syntax, check to see if its a name
            if args.verbos:
                cerr.write(b'[*] running name translation for ' + args.addr.encode('utf-8') + b'...\n')
                cerr.flush()
            #set addr to a valid bluetooth address
            addr = bt_dns(args.addr)
            if addr == None:
                #we couldnt figure out the name error out
                cerr.write(b'ERROR: invalid address reviced, unable to translate name is the device discoverable?\n')
                quit()

        #set up the arguments to pass to the listen thread
        thread_args = [sock,addr]
        
        #conect to the target address
        if args.verbos:
            cerr.write(b'[*] connecting to ' + args.addr.encode('utf-8') + b'\n')
            cerr.flush
        sock.connect((addr,port))
        if args.verbos:
            cerr.write(b'[*] connected!\n')
            cerr.flush()
    #were running as the server
    else:
        if args.addr != None:
            #only change the target address if the user gave us one to change to
            args = args.addr
        #this is the set up for the server will need to be bound to a bool function in the args
        sock.bind((addr,port))
        sock.listen(1)
        if args.verbos:
            cerr.write(b'[*] waiting for connections...\n')
            cerr.flush()
        client_sock, c_addr = sock.accept()
        if args.verbos:
            cerr.write(b'[*] recived connection from [' + c_addr[0].encode('utf-8') + b']!\n')
            cerr.flush()
        thread_args = [client_sock,c_addr]
    
    #start the net thread to recv info without preventing us from getting input
    nt = net_thread()
    nt.set_client(thread_args,[cin,cout,cerr],size)
    nt.start()

    if args.chat:
        msg = cin.readline()
    else:
        msg = cin.read(size) 
    #now the reason that we have the while true loops duplicted is so we mitigate the number of calculations
    #of if statements inside of the loops
    if args.listen:
        #were the server, send data on a socket that we are not using
        while True:
                client_sock.send(msg)
                if args.chat:
                    msg = cin.readline()
                else:
                    msg = cin.read(size)
        client_sock.close()    
    else:
        #were the client, send data on the same socket that we recive it
        while True:
            sock.send(msg)
            if args.chat:
                msg = cin.readline()
            else:
                msg = cin.read(size)
    sock.close()
if __name__ == '__main__':
    main()
