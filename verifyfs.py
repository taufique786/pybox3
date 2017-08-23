#Program by Taufique

import clc
import paramiko
import sys
import time
import colorama
import logging
import calendar
import datetime
import Tkinter as tk
import threading
import getpass
import os
from timeit import default_timer

#Log to file
logging.basicConfig(filename='log.txt',level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.critical('This is a critical message.')
logging.error('This is an error message.')
logging.warning('This is a warning message.')
logging.info('This is an informative message.')
logging.debug('This is a low-level debug message.')

#Color coding the output
colorama.init()
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


while True:
	# Ask for credentials.  These are the same credentials used to login to the web UI (https://control.ctl.io)
	api_key = raw_input ("Please enter your Control V1 API Key: ")
	api_pass = getpass.getpass("Please enter your Control V1 API Password: ")

	clc.v1.SetCredentials(api_key,api_pass)
	try:
		clc.v1.Account.GetAlias()
		break
	except Exception, e:
		print bcolors.FAIL + "Incorrect credentials. Try again!" + bcolors.ENDC
	
#Ask for the server list
print bcolors.HEADER + bcolors.BOLD + "Select your server list text file" + bcolors.ENDC
from Tkinter import Tk
from tkFileDialog import askopenfilename
Tk().withdraw()
filename = askopenfilename()
getIp = None
getCreds = None

def GetServerDetails(alias,servers):
	global getIp
	global getCreds
	getCreds = clc.v1.Server.GetCredentials(servers=servers,alias=alias)
	getIp = clc.v1.Server.GetServerDetails(alias=alias, servers=servers)

#Empty the file
with open('output.txt', 'w'):pass

print bcolors.HEADER + bcolors.BOLD + "Verifying disk I/O errors" + bcolors.ENDC
# Read file
with open(filename, 'r') as servlist:
    for line in servlist:
	clclist = line.split()
	print "\n" + bcolors.UNDERLINE + str(clclist) + bcolors.ENDC
	
	#Guess the alias
	try:
		guessAlias = clc.v1.Account.GetAccountDetails(alias=line[3:5])
	except:
		pass
	try:
		guessAlias = clc.v1.Account.GetAccountDetails(alias=line[3:6])
	except:
		pass
	try:
		guessAlias = clc.v1.Account.GetAccountDetails(alias=line[3:7])
	except:
		pass
	
	getAlias = guessAlias['AccountAlias']
	
	#Get server credentials and server details
	server_details_thread = threading.Thread(target=GetServerDetails,args=(getAlias,clclist))
	server_details_thread.setDaemon(True)
	server_details_thread.setName('server details')
	server_details_thread.start()
	start = default_timer()
	while(server_details_thread.is_alive() and (default_timer() - start)<5.0):
		print 'Getting server details',time.asctime( time.localtime(time.time()) )
		time.sleep(1)

	if(server_details_thread.is_alive()):
		print bcolors.FAIL + 'Not found. The server is either deleted or incorrect' + bcolors.ENDC
		f = open('output.txt', 'a')
		f.write(str(clclist) + ' Not found. The server is either deleted or incorrect' + "\n")
		f.close()
		time.sleep(2)
		continue
	creds = getCreds[0]['Password']
	ipaddr = getIp[0]['IPAddress']

	#Login and touch the file
	#Setting parameters like host IP, username, and passwd
	HOST = ipaddr 
	USER = "root"
	PASS = creds
	#A function that logins and execute commands
	def fn():
		for ips in getIp:
  			#Connect to server
  			try:
				command = 'if [ -w {filename} ]; then echo OK!; else echo NOT OK; fi;'
        	                command = command.format(filename='/etc/passwd')
	                        client1=paramiko.SSHClient()
                	        #Add missing client key
                        	client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        	#connect to server
				client1.connect(HOST,username=USER,password=PASS,timeout=2)
			except Exception, e:
				print bcolors.FAIL + "[-] Connection Failed. Unreachable" + bcolors.ENDC
				f = open('output.txt', 'a')
				f.write(str(clclist) + ' [-] Connection Failed. Unreachable' + "\n")
				f.close()
				continue
			#Gather commands and read the output from stdout
			try:
  				stdin, stdout, stderr = client1.exec_command(command)
				result = stdout.readline().rstrip()
  				print bcolors.OKGREEN + result + bcolors.ENDC
				f = open('output.txt', 'a')
				f.write(str(clclist) + result + "\n")
				f.close()
			except:
				print bcolors.FAIL + 'FAILED' + stderr.read() + bcolors.ENDC
				f = open('output.txt', 'a')
				f.write(str(clclist) + 'FAILED' + "\n")
				f.close()
  			client1.close()

	showOut = fn()

os.startfile('output.txt')
exit()
