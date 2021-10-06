from datetime import time
from db_model import network_device
import os
from flask import Flask, render_template, flash, url_for, redirect, send_file
from wtforms.form import FormMeta
from forms import DeviceDiscoveryForm
from discovery import *  
from get_dumps import *
from parse_files import *
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output 
import pandas
import shutil
import pickle
import subprocess
import webbrowser
from flask_sqlalchemy import SQLAlchemy
import db_model


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ed318f035ce728eed6084dfefaa06545'  #used for anty TCP-Highjacking in flask
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dump_db.sqlite3'
app.config ['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

OUTPUT_DIR ="./output"
DUMP_DIR = "./dump"

reachable = []
username = ""
password = ""
ip_network = ""
ssh_enabled_ips = []
dump_data = {}
excelfiles = 0
config_files = 0


def number_dump_files():
    num = 0
    try:
        files = os.listdir(DUMP_DIR)
        for file in files:
            if "_command.txt" in file:
                num += 1
        return(num)
    except Exception as e:
        return (0)

def number_excelfiles():
    num = 0
    try:
        files = os.listdir(f"{DUMP_DIR}/parsed")
        for file in files:
            if ".xlsx" in file:
                num += 1
        return(num)
    except Exception as e:
        return (0)

def get_status():
    number_of_dumpfiles = number_dump_files()
    number_of_excelfiles = number_excelfiles()
    status={"number_of_dumpfiles":number_of_dumpfiles,
            "excelfiles":number_of_excelfiles,
            "networkdevices":len(network_device.query.all())}
    return(status)

def GetDevicesFromDB():
    networkdevices = []
    for db_device in network_device.query.all():
        device={}
        device["host"]=db_device.device_ip
        device["hostname"]=db_device.device_name
        device["auth_strict_key"]=False
        device["transport"]="paramiko"
        device["type"]=db_device.device_type
        device["auth_username"]=db_device.device_username
        device["auth_password"]=db_device.device_password
        device["enabled"]=db_device.device_enabled
        networkdevices.append(device)
    return(networkdevices)
         

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
        global networkdevices, username, password,reachable 
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
                hostname = hostname.split("@")[1]
        else:
            hosttype = "other"
        #### Now in DB  ####
        #device = {"host":IP,
        #    "hostname":hostname[:-1],
        #    "auth_username":username,
        #    "auth_password":password,
        #    "type":hosttype,
        #    "transport":"paramiko",
        #    "auth_strict_key": False,
        #    "enabled":True
        #    }
        #networkdevices.append(device)

        # Add Device to Database (network_device)
        db_device=network_device(
            device_name=hostname[:-1],
            device_ip=IP,
            device_username=username,
            device_type=hosttype,
            device_enabled=True,
            device_password=password)
        db.session.add(db_device)
        db.session.commit()
        reachable = []

    except Exception as e:
        print (e)
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
    global networkdevices, reachable
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
    content=get_status()
    return render_template("index.html",status=content)

@app.route("/device_discovery", methods=['GET', 'POST'])
def device_discovery():
    global ip_network,username,password
    reachable = []
    ssh_enabled_ips = []
    form = DeviceDiscoveryForm()
    if form.validate_on_submit():
        username=form.username.data
        password=form.password.data
        ip_network=form.ip_network.data
        if not check_ip_network(ip_network):
            flash(f'non valid IPv4 Network: {ip_network}', 'danger')
            return redirect(url_for('device_discovery'))
        else:
            # flash(f'Device Discovery is Startet...', 'success')
            return redirect(url_for('progress'))
    content=get_status()
    return render_template("device_discovery.html",form=form,title="Device Discovery",status=content)

@app.route("/about")
def about():
    content=get_status()
    return render_template("about.html",status=content) 

@app.route("/dump")
def dump():
    networkdevices = GetDevicesFromDB()
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
    files = os.listdir(DUMP_DIR)
    try:
        files.remove("parsed")
        files.remove("running")
    except Exception:
        pass
    #Parsing the Dump-Files
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
                #print(parsed_output)
                if parsed_output==("Error","Error"):  #Error in parsing, Next Commmand
                   #print("Error while Parsing")
                   continue
                try: 
                    key=parsed_output[0].replace(" ","_")
                except TypeError:
                    print ("Error in parsing")
                    continue
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
    shutil.make_archive("./output/NetworkDump", 'zip', "./dump") # create NetworkDump.zip from folder dump
    pickle.dump(dump_data, open("dump_data.pickle", "wb")) # save 'dump_data' dictonary to file
    content=get_status()
    return render_template("parse.html",status=content)

@app.route("/progress")
def progress():
    global username, password, ip_network, ssh_enabled_ips
    content=get_status()
    render_template("/progress.html", ip_network=ip_network, title="TCP Scan", hosts=ssh_enabled_ips,status=content)
    ssh_enabled_ips=[]
    #form = DeviceDiscoveryForm()
    ssh_enabled_ips=tcpscan(ip_network)
    unique_ips = list(set(ssh_enabled_ips))
    try_logon(unique_ips)
    content=get_status()
    return render_template("/progress_logon.html",status=content)

@app.route("/device_view")
def device_view():# Not working Now
    netdevices = network_device.query.all()
    content=get_status()
    return render_template("/device_view.html", status=content, devices=netdevices)

@app.route("/download_dump")
def download_dump():
    # Export dump_data
	path = "./output/NetworkDump.zip"
	return send_file(path, as_attachment=True)

@app.route("/draw_diagram")
def draw_diagram():
    #Run graphs.py this generates the drawing, Check if its allready running
    
    command = 'ps aux|grep graphs.py'
    ps = subprocess.Popen(command,shell=True, stdout = subprocess.PIPE) 
    output_ps=str(ps.communicate()).split("'")[1]
    print (f"*** Output Grep ***\n{output_ps}\n***********")
    if "python" and  "graphs.py" in output_ps:
        print ('**** Already Running ****')
        for line in output_ps.split("\n"):
            print(f"Line : {line} ")
            if "python" and  "graphs.py" in line:
                proc = line.split(" ")
                kill_command=f"kill {proc}"
    if os.path.exists("dump_data.pickle"):
        process = subprocess.Popen(['python', 'graphs.py'])
        webbrowser.open_new_tab('http://localhost:8050')
        content=get_status()
        return render_template("parse.html",status=content)
    else:
        content=get_status()
        if (content["excelfiles"]<=1 or content["number_of_dumpfiles"]<=1) and content["networkdevices"]>=1:
            return redirect('/dump')
        else:   

            return redirect('/device_discovery')

@app.route("/delete")
def delete():
    #delete DB entries
    db.session.query(network_device).delete()
    db.session.commit()
    #delete dump directory
    if os.path.exists("./dump"):
        shutil.rmtree("./dump", ignore_errors=False, onerror=None)
    #create empty dump directory
    path = os.path.join("./","dump")
    os.mkdir(path) #delete dump directory
    if os.path.exists("./output"):
        shutil.rmtree("./output", ignore_errors=False, onerror=None)
    #create empty dump directory
    path = os.path.join("./","output")
    os.mkdir(path)
    #delete pickel file for data export to graph
    if os.path.exists("dump_data.pickle"):
        os.remove("dump_data.pickle")
    flash('All device data deleted', 'success')
    content=get_status()
    return redirect ("device_view")

if __name__ == "__main__":
    app.run(host="0.0.0.0")   #Needet when Container is used