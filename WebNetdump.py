from datetime import time
import os
from flask import Flask, render_template, flash, url_for, redirect, send_file
from wtforms.form import FormMeta
from wtforms.validators import HostnameValidation
from forms import DeviceDiscoveryForm
from discovery import *  
from get_dumps import *
from parse_files import *
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output 
import pandas
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ed318f035ce728eed6084dfefaa06545'  #used for anty TCP-Highjacking in flask
OUTPUT_DIR ="./output"
DUMP_DIR = "./dump"

networkdevices = []
reachable = []
username = ""
password = ""
ip_network = ""
ssh_enabled_ips = []
dump_data = {}
excelfiles = 0
config_files = 0

#Task have share Global Vars have to be in Main-App
def worker_ssh_test(IP):
    global reachable
    if tcpping(str(IP),22,4):
        reachable.append(str(IP))
    return  

def worker_ssh_logon(IP):
    ###  Login and add device_dict to networkdevices
    try:
        device={}
        global networkdevices, username, password
        ssh = ConnectHandler(device_type="cisco_ios", ip=IP, username=username, password=password)
        hostname = ssh.find_prompt()
        sh_ver = ssh.send_command("show version")
        username_len = len(username)
        if " IOS XE " in sh_ver:
            hosttype = "ios-xe"
        elif " IOS " in sh_ver:
            hosttype = "cisco_ios"
        elif "NX-OS" in sh_ver:
            hosttype = "cisco_nxos_ssh"
        elif hostname[:username_len+1] == username+"@":
            ssh.disconnect()
            ssh_session = ConnectHandler(device_type="paloalto_panos", ip=IP, username=username, password=password)
            testpalo = ssh_session.send_command("show system info")
            if "model: PA-" in testpalo:
                hosttype = "palo"
        else:
            hosttype = "other"
        device = {"host":IP,
            "hostname":hostname[:-1],
            "auth_username":username,
            "auth_password":password,
            "type":hosttype,
            "transport":"paramiko",
            "auth_strict_key": False,
            "enabled":True
            }
        networkdevices.append(device)
    except Exception as e:
        pass
    return

def tcpscan(ip_network):
    global reachable
    ''' do a TCP-Scan on an IPv4 Network'''
    ip_list = list(ipaddress.IPv4Network(ip_network).hosts())
    if len(ip_list) < 75:
        num_threads = len(ip_list)
    else:
        num_threads = 75
    threads = ThreadPool( num_threads )
    results = threads.map( worker_ssh_test, ip_list )
    threads.close()
    threads.join()
    return(reachable)

def try_logon(ip_list):
    global networkdevices
    '''do a SSH Logon to all SSH Enabled Devices'''
    if len(ip_list) < 75:
        num_threads = len(ip_list)
    else:
        num_threads = 75
    threads = ThreadPool( num_threads )
    results = threads.map( worker_ssh_logon, ip_list )
    threads.close()
    threads.join()

def add_to_data(key,data,hostname):
    global dump_data
    if key not in  dump_data.keys():
        dump_data[key]=[]
    for line in data:
        item ={}
        item['Devicename']=hostname
        for k in line.keys():
            item[k]=line[k]
        dump_data[key].append(item)

def add_to_data_vrf(key,data,hostname,vrf):
    global dump_data
    if key not in  dump_data.keys():
        dump_data[key]=[]
    for line in data:
        item ={}
        item['Devicename']=hostname
        item['vrf']=vrf
        for k in line.keys():
            item[k]=line[k]
        dump_data[key].append(item)

@app.route("/")
def index():
    return render_template("index.html",number_of_devices=len(networkdevices),excelfiles=excelfiles)

@app.route("/device_discovery", methods=['GET', 'POST'])
def device_discovery():
    global username, password, ip_network
    reachable = []
    ssh_enabled_ips = []
    form = DeviceDiscoveryForm()
    if form.validate_on_submit():
        username=form.username.data
        password=form.password.data
        ip_network=form.ip_network.data
        if not check_ip_network(ip_network):
            flash(f'non valid IPv4 Network: {ip_network}', 'error')
            return redirect(url_for('device_discovery'))
        else:
            flash(f'Device Discovery is Startet...', 'success')
            return redirect(url_for('progress'))
    return render_template("device_discovery.html",form=form,title="Device Discovery",number_of_devices=len(networkdevices))

@app.route("/about")
def about():
    return render_template("about.html",number_of_devices=len(networkdevices))

@app.route("/parse")
def parse():
    OUTPUT_DIR="./dump/parsed"
    # if no dum exists, create one
    if not os.path.exists("./dump"):
        return redirect(url_for('dump'))
    files = os.listdir(DUMP_DIR)  
    for file in files:
        nos = "ios"
        filename = f"{DUMP_DIR}/{file}"
        print(f"Parsing File: {file}")
        if "_originalFiles.txt" in filename:
            with open(filename) as f:
                originated_path=f.read().split(" ")[-1]
            continue
        hostname = file[:-12]
        try: 
            with open(filename) as f:
                data = f.read()
            #### Split Large Snapshot file to Command-List with Output ####
            commands = split_commands(data)

            ### Create "parsed" Folder if not exist ###
            if os.path.exists(OUTPUT_DIR):  
                pass
            else:
                path = os.path.join(DUMP_DIR,"parsed")
                os.mkdir(path)
            outputfile = f"{OUTPUT_DIR}/{file[:-12]}_parsed.json"
            with open(outputfile, "w") as outfile:
                outfile.write("")

            for command in commands:
                ### Run Parser, get back Command and Json as Tuble, if worked  ###
                if command == "":
                    continue
                if "show version\n" in command:
                    if "NX-OS" in command:
                        nos="nxos"
                if "show system info\n" in command:
                    nos="panos"
                parsed_output = parse_textfsm(command,file,nos) 
                if parsed_output==("Error","Error"):  #Error in parsing, Next Commmand
                    continue
                key=parsed_output[0].replace(" ","_")
                if parsed_output[2] != '':  # vrf in command 
                    add_to_data_vrf(key,parsed_output[1],hostname,parsed_output[2])
                else:
                    add_to_data(key,parsed_output[1],hostname)

                with open(outputfile, "a") as f:
                    f.write(f"{parsed_output[0]}:\n{str(parsed_output[1])}\n")
        except IsADirectoryError:
            pass  
    excelfiles = 0
    for k in dump_data.keys():
        try: 
            if dump_data[k] == []:
                continue
            df = pandas.DataFrame(dump_data[k])
            df.to_excel(f"{OUTPUT_DIR}/{k}.xlsx")
            print (f"Generated {k} Excel-File")
            excelfiles += 1
        except Exception as e:
            print (e)
    shutil.make_archive("./output/NetworkDump", 'zip', "./dump")
    return render_template("parse.html",number_of_devices=len(networkdevices),excelfiles=excelfiles)

@app.route("/dump")
def dump():
    if len(networkdevices) == 0:
        redirect ("device_discovery")
    # delete directory if old dumps exist and create new dir
    if os.path.exists("./dump"):
        shutil.rmtree("./dump", ignore_errors=False, onerror=None)
    path = os.path.join("./","dump")
    os.mkdir(path)
    if len(networkdevices) <= 50 :
        num_threads=len(networkdevices)
    else:
        num_threads=50

    threads = ThreadPool( num_threads )
    results = threads.map( dump_worker, networkdevices )
    threads.close()
    threads.join()
    print (networkdevices)
    return render_template("dump.html",number_of_devices=len(networkdevices))

@app.route("/progress")
def progress():
    global username, password, ip_network, ssh_enabled_ips, networkdevices
    ssh_enabled_ips=[]
    form = DeviceDiscoveryForm()
    ssh_enabled_ips=tcpscan(ip_network)
    return render_template("progress.html", ip_network=ip_network, title="TCP Scan", hosts=ssh_enabled_ips)

@app.route("/progress_logon") 
def progress_logon():
    global ssh_enabled_ips
    unique_ips = list(set(ssh_enabled_ips))
    ssh_enabled_ips = []
    reachable = []
    try_logon(unique_ips)
    with open(f"{OUTPUT_DIR}/Networdevices.txt","w") as f:
        for device in networkdevices:
            f.write(f"{device['hostname']},{device['host']},{device['type']},{device['enabled']}\n")
    return render_template("/progress_logon.html",number_of_devices=len(networkdevices))

@app.route("/device_view")
def device_view():# Not working Now
    return render_template("/device_view.html", networkdevices=networkdevices)

@app.route("/download_dump")
def download_dump():
	#path = "html2pdf.pdf"
	#path = "info.xlsx"
	path = "./output/NetworkDump.zip"
	#path = "sample.txt"
	return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0")