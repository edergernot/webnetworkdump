def split_commands(text):
    lines = text.split("\n")
    command_seperator=[]
    for index in range(0,len(lines)):
        if lines[index] == '****************************************':
            command_seperator.append(index)
    commands=[]
    for index in range(0,len(command_seperator)):
        if index == len(command_seperator)-1:  #last command in file
            command = lines[command_seperator[index]+1:]
        else:
            command = lines[command_seperator[index]+1:command_seperator[index+1]]
        output = "\n".join(command)
        commands.append(output)
    return commands


def parse_textfsm(data,file,nos):
    from ntc_templates.parse import parse_output 
    import os
    device_name=file[:-12]
    RUN_DIR="./dump/running"
    vrf = ""
    platform=get_devtype_from_deb(device_name)
    text=data.split('**----------------------------------------**')
    if len(text) <= 1:  # No usefull data
        return 
    command=text[0][:-1]
    if "show ip arp vrf" in command:
        vrf = command.split(" ")[-1]
        command = "show ip arp"
    raw_cli_output=text[1]
    if platform == "nxos":
        platform="cisco_nxos"
    elif platform == "ios-xe":
        platform="cisco_ios"
    elif platform == "palo":
        platform="paloalto_panos"
    elif platform == "asa":
        platform="cisco_asa"
    if "show running" in command:
        if not os.path.isdir(RUN_DIR):
            os.makedirs(RUN_DIR)
        runnningfile = f"{RUN_DIR}/{device_name}_running.txt"
        with open(runnningfile,"w") as f:
            f.write(raw_cli_output) 
    if "show config running" in command:
        if not os.path.isdir(RUN_DIR):
            os.makedirs(RUN_DIR)
        runnningfile = f"{RUN_DIR}/{device_name}_running.txt"
        with open(runnningfile,"w") as f:
            f.write(raw_cli_output) 
    try:    
        parsed_output = parse_output(platform=platform, command=command, data=raw_cli_output)
    except Exception as e:
        #print(e)
        return("Error","Error")
    return(command, parsed_output, vrf)


def convert_dbnos_genienos(db_nos):
    if db_nos == "ios":
        return ("ios")
    elif db_nos == "ios-xe":
        return ("iosxe")
    elif db_nos == "asa":
        return ("asa")
    else:
        return ()
        
def get_devtype_from_deb (device_name): #queries the db for devicetype
    from sqlalchemy import create_engine
    from sqlalchemy import text
    engine = create_engine('sqlite:///dump_db.sqlite3')
    with engine.connect() as connection:
        result = connection.execute(text(f"select * from network_device where device_name='{device_name}'"))
        for r in result:
            device_type = r['device_type']
    return (device_type)
