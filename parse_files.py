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
    RUN_DIR="./dump/running"
    vrf = ""
    platform="cisco_ios"
    text=data.split('**----------------------------------------**')
    if len(text) <= 1:  # No usefull data
        return 
    command=text[0][:-1]
    if "show ip arp vrf" in command:
        vrf = command.split(" ")[-1]
        command = "show ip arp"
    raw_cli_output=text[1]
    if nos == "nxos":
        platform="cisco_nxos"
    if nos == "iosxe":
        platform="cisco_ios"
    if nos == "panos":
        platform="paloalto_panos"
    if nos == "asa":
        platform="cisco_asa"
    if "show running" in command:
        if not os.path.isdir(RUN_DIR):
            os.makedirs(RUN_DIR)
        runnningfile = f"{RUN_DIR}/{file[:-12]}_running.txt"
        with open(runnningfile,"w") as f:
            f.write(raw_cli_output) 
    if "show config running" in command:
        if not os.path.isdir(RUN_DIR):
            os.makedirs(RUN_DIR)
        runnningfile = f"{RUN_DIR}/{file[:-12]}_running.txt"
        with open(runnningfile,"w") as f:
            f.write(raw_cli_output) 
    try:    
        parsed_output = parse_output(platform=platform, command=command, data=raw_cli_output)
    except Exception as e:
        print(e)
        return("Error","Error")
    return(command, parsed_output, vrf)

