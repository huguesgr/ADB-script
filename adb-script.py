#!/usr/bin/python

import subprocess, time, re, smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

###### CONFIGURATION ######
# TO DO
###########################

def device_name():
	proc = subprocess.Popen(["adb", "shell", "cat" ,"/system/build.prop"], stdout=subprocess.PIPE)
	(out, err) = proc.communicate()
	out = out.decode("utf-8").split("\r\n")
	manufacturer, model, id = "-", "-", "-"
	for line in out:
		if "ro.product.manufacturer" in line:
			manufacturer = line.split("=")[1]
		elif "ro.product.model" in line:
			model = line.split("=")[1]
		elif "ro.build.id" in line:
			id = line.split("=")[1]
	return manufacturer+"_"+model+"_"+id+"_"+time.strftime("%d-%m-%Y_%H-%M-%S")
	
def prompt_email_and_send(attach, type):
	msg = MIMEMultipart()
	
	msg['From'] = "testunps@gmail.com"
	msg['To'] = input("Your email address?")
	msg['Subject'] = "ADB-script Logs - "+device_name()+" - "+type

	msg.attach(MIMEText("Here are your logs."))
	part = MIMEBase('application', 'octet-stream')
	part.set_payload(open(attach, 'rb').read())
	encoders.encode_base64(part)
	part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attach))
	msg.attach(part)

	try:
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.ehlo()
		server.starttls()
		server.login("testunps@gmail.com", "testunps1234")
		print("Sending mail... This might take a while.")
		server.sendmail('testunps@gmail.com', msg['To'], msg.as_string())
		server.quit()
		print("Successfully sent email.")
	except SMTPException:
	   print("Error: unable to send email.")

def device_status():
	proc = subprocess.Popen(["adb", "devices", "-l"], stdout=subprocess.PIPE)
	(out, err) = proc.communicate()
	out=out.decode("utf-8")
	if out.find("device:")!=-1:
		return "detected"
	elif out.find("unauthorized")!=-1:
		return "unauthorized"
	else:
		return "no_device"
		
def detect_device():
	if(device_status()=="no_device"):
		print("Please plug a device...")
		while(device_status()=="no_device"):
			time.sleep(1)
	if(device_status()=="unauthorized"):
		print("You need to authorize access on the device.")
		while(device_status()=="unauthorized"):
			time.sleep(1)

def nfc_logs(output):
	found = False
	for line in output:
		if re.match("4e[ ]?46[ ]?43", line, re.IGNORECASE) or re.match("01[ ]?0c[ ]?00", line, re.IGNORECASE) or re.match("4a[ ]?53[ ]?52", line, re.IGNORECASE):
			print(line)
			found = True
	return found

print("")
detect_device()
print(device_name())

print("Available options:\n")
print("[1] build.prop: ro.product vars")
print("[2] main + radio logs [buffer] (with NFC API check)")
print("[3] main logs [live]")
print("")
nb = str(input('Choose option: '))
print("")

# Difference if script is launch from Python script or .exe
if os.getcwd()[-10:]=="ADB-script":
	file_path = os.getcwd()+'/logs/'
else:
	file_path = os.path.dirname(os.getcwd())+'/logs/'

# Creating logs folder
if not os.path.exists(file_path): os.makedirs(file_path)

# Adding device name for log files
file_path += device_name()

if nb=="1":
	proc = subprocess.Popen(["adb", "shell", "cat" ,"/system/build.prop"], stdout=subprocess.PIPE)
	(out, err) = proc.communicate()
	out = out.decode("utf-8").split("\r\n")
	for line in out:
		if "ro.product.model" in line or "ro.product.manufacturer" in line:
			print(line)
			
elif nb=="2":
	proc = subprocess.Popen(["adb", "logcat", "-v" ,"time", "-d"], stdout=open(file_path+"_main.txt", 'w'))
	(out, err) = proc.communicate()
	out_main = open(file_path+"_main.txt", 'r')
	proc = subprocess.Popen(["adb", "logcat", "-b", "radio", "-v" ,"time", "-d"], stdout=open(file_path+"_radio.txt", 'w'))
	(out, err) = proc.communicate()
	out_radio = open(file_path+"_radio.txt", 'r')
	
	found = nfc_logs(out_main) or nfc_logs(out_radio)
	
	if not(found):
		print("Logs are clean of NFC APDU exchanges.")
	
	email = input("Send logs by email? (y/n)")
	if email=="y":
		prompt_email_and_send(file_path+"_main.txt", 'main')
		prompt_email_and_send(file_path+"_radio.txt", 'radio')
	
elif nb=="3":
	try:
		proc = subprocess.Popen(["adb", "logcat", "-v" ,"time"], stdout=open(file_path+"_main.txt", 'w'))
		print("Press CTRL+C to stop log capture.")
		proc.wait()
	except KeyboardInterrupt:
		proc.terminate()	
	email = input("Send logs by email? (y/n)")
	if email=="y":
		prompt_email_and_send(file_path+"_main.txt", 'main')
		
else:
	print("Invalid choice.")

input("\nPress Enter to exit.")

# WINDOWS only
path = os.path.dirname(os.getcwd())+"\logs"
subprocess.Popen('explorer "{0}"'.format(path))
