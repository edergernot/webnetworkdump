COMMANDS = ["show clock",
            "show version",
            "show running",
            "show inventory",
            "show cdp neighbors detail",
            "show ip interface brief",
            "show interfaces",
            "show interface trunk",
            "show interfaces status",
            "show etherchannel summary",
            "show mac address-table",
            "show ip route",
            "show arp",
            "show access-lists",
            "show ip arp",
            "show ip protocols",
            "show ip route",
            "show ipv6 route",
            "show ipv6 neighbors"
            "show ip mroute",
            "show power inline",
            "show standby all",
            "show ip vrf",
            "show lldp",
            "show lldp neighbors detail",
            "show processes cpu history",
            "show ip pim interface",
            "show ip pim neighbor",
            "show ntp associations",
            "show ntp status",
            "show environment",
            "show environment all",
            "show environment power",
            "show environment temperature",
            "show spanning-tree",
            "show spanning-tree detail",
            "show license all",
            "show stormcontroll",
            "show vlan",
            "show vtp status",
            "show vtp password",
            "show mka summary",
            "show authentication sessions"
            ]

VRF_COMMANDS = ["show ip route vrf <VRF>",
                "show ipv6 route vrf <VRF>",
                "show ip mroute vrf <VRF>",
                "show ip arp vrf <VRF>",
                "show ip protocols vrf <VRF>"
                ]

NX_COMMANDS = ["show vpc",
               "show port-channel summary",
               "show fex",
               "show interface",
               "show interface status"
               ]

PALO_COMMANDS = ["show system info",
                 "show interface all",
                 "show interface logical",
                 "show arp all",
                 "show routing route",
                 "show config running",
                 "show global-protect-gateway current-user",
                 "show global-protect-gateway previous-user",
                 "show global-protect-gateway statistics",
                 "show session meter"
                 ]

ASA_COMMANDS = ["show clock",
            "show version",
            "show running",
            "show inventory",
            "show interface detail",
            "show interface",
            "show route",
            "show ospf",
            "show ospf neighbor",
            "show bgp summary",
            "show arp",
            "show vpn-sessiondb",
            "show vpn-sessiondb detail l2l",
            "show vpn-sessiondb anyconnect",
            "show failover",
            "show asp drop",
            "show name",
            "show xlate",
            "show running-config object network",
            "show ipv6 route",
            "show ipv6 neighbor",
            "show ipv6 ospf"]



def dump_worker(device:dict):   #  Main Thread for SSH-Session and File creation
    try:
        from scrapli.driver.core  import  NXOSDriver
        from scrapli.driver.core.cisco_iosxr.sync_driver import IOSXRDriver
        from netmiko import ConnectHandler
        OUTPUT_DIR="./dump"
        vrf_enabled = False
        is_nx_os = False
        device_type = device.pop("type")
        hostname = device.pop("hostname")
        enabled = device.pop("enabled")
        #print(f"{hostname} : {device_type}")
        if device_type == "other":
            return
        if not enabled:
            return
        if device_type == "cisco_nxos_ssh":   # Connect to Nexus
            ssh_session = NXOSDriver(**device)
            ssh_session.open()
            hostfilename = hostname +"_command.txt"
            with open (f"{OUTPUT_DIR}/{hostfilename}","w") as outputfile:
                outputfile.write("\n")
                outputfile.write("*"*40)
                outputfile.write("\n")  
                for command in COMMANDS:
                    outputfile.write(command)
                    outputfile.write("\n")
                    outputfile.write("**"+"-"*40+"**")
                    outputfile.write("\n")
                    commandoutput = ssh_session.send_command(command)
                    if command == "show ip vrf":
                        if len(commandoutput.split("\n")) >= 2:
                            vrf_enabled = True
                            vrf_output = commandoutput.result
                            print (vrf_output) #Debug
                    outputfile.write(commandoutput.result) 
                    outputfile.write("\n")
                    outputfile.write("*"*40)
                    outputfile.write("\n")
                    
                if vrf_enabled:
                    vrfs=[]
                    for line in vrf_output.split("\n"):
                        if line.split(" ")[0] == "Name":
                            continue
                        if line[4] == " ":
                            continue
                        vrf = line.split(" ")[2]
                        vrfs.append(vrf)
                    for vrf in vrfs:
                        for command in VRF_COMMANDS:
                            command_vrf = command.replace("<VRF>", vrf)
                            outputfile.write(command_vrf)
                            outputfile.write("\n")
                            outputfile.write("**"+"-"*40+"**")
                            outputfile.write("\n")
                            commandoutput = ssh_session.send_command(command_vrf)
                            outputfile.write(commandoutput.result) 
                            outputfile.write("\n")
                            outputfile.write("*"*40)
                            outputfile.write("\n")

                for nx_command in NX_COMMANDS:     
                    outputfile.write(nx_command)
                    outputfile.write("\n")
                    outputfile.write("**"+"-"*40+"**")
                    outputfile.write("\n")
                    nx_commandoutput = ssh_session.send_command(nx_command)
                    outputfile.write(nx_commandoutput.result) 
                    outputfile.write("\n")
                    outputfile.write("*"*40)
                    outputfile.write("\n")
        
        #### Do commands on Palo ####
        elif device_type == "palo":
            hostip=device["host"]
            user = device["auth_username"]
            pwd = device["auth_password"]
            ssh_session = ConnectHandler(device_type="paloalto_panos", ip=hostip, username=user, password=pwd)
            prompt = ssh_session.find_prompt()
            hostname = prompt.split("@")[1]
            hostfilename = hostname[:-1] +"_command.txt"
            with open (f"{OUTPUT_DIR}/{hostfilename}","w") as outputfile:
                outputfile.write("\n")
                outputfile.write("*"*40)
                outputfile.write("\n") 
                for command in PALO_COMMANDS:
                    outputfile.write(command)
                    outputfile.write("\n")
                    outputfile.write("**"+"-"*40+"**")
                    outputfile.write("\n")
                    commandoutput = ssh_session.send_command(command)
                    outputfile.write(commandoutput) 
                    outputfile.write("\n")
                    outputfile.write("*"*40)
                    outputfile.write("\n")
                ssh_session.disconnect()
        
        #### Do commands on Cisco ASA ####
        elif device_type == "asa":
            hostip=device["host"]
            user = device["auth_username"]
            pwd = device["auth_password"]
            ssh_session = ConnectHandler(device_type="cisco_asa", ip=hostip, username=user, password=pwd)
            prompt = ssh_session.find_prompt()
            hostfilename = hostname +"_command.txt"
            with open (f"{OUTPUT_DIR}/{hostfilename}","w") as outputfile:
                outputfile.write("\n")
                outputfile.write("*"*40)
                outputfile.write("\n") 
                for command in ASA_COMMANDS:
                    outputfile.write(command)
                    outputfile.write("\n")
                    outputfile.write("**"+"-"*40+"**")
                    outputfile.write("\n")
                    commandoutput = ssh_session.send_command(command)
                    outputfile.write(commandoutput) 
                    outputfile.write("\n")
                    outputfile.write("*"*40)
                    outputfile.write("\n")
                ssh_session.disconnect()

        ## 
        else:
            ssh_session = IOSXRDriver(**device)
            ssh_session.open()
            hostfilename = hostname +"_command.txt"
            with open (f"{OUTPUT_DIR}/{hostfilename}","w") as outputfile:
                outputfile.write("\n")
                outputfile.write("*"*40)
                outputfile.write("\n") 
                for command in COMMANDS:
                    outputfile.write(command)
                    outputfile.write("\n")
                    outputfile.write("**"+"-"*40+"**")
                    outputfile.write("\n")
                    commandoutput = ssh_session.send_command(command)
                    if command == "show ip vrf" and len(commandoutput.result.split("\n")) > 2:
                        vrf_enabled = True
                        vrf_output = commandoutput.result
                    outputfile.write(commandoutput.result) 
                    outputfile.write("\n")
                    outputfile.write("*"*40)
                    outputfile.write("\n")
                if vrf_enabled:
                    vrfs=[]
                    for line in vrf_output.split("\n"):
                        if len(line.split(" ")) < 4:
                            continue
                        if line.split(" ")[2] == "Name":
                            continue 
                        if line[4] == " ":
                            continue
                        vrf = line.split(" ")[2]
                        vrfs.append(vrf)
                    for vrf in vrfs:
                        for command in VRF_COMMANDS:
                            command_vrf = command.replace("<VRF>", vrf)
                            outputfile.write(command_vrf)
                            outputfile.write("\n")
                            outputfile.write("**"+"-"*40+"**")
                            outputfile.write("\n")
                            commandoutput = ssh_session.send_command(command_vrf)
                            outputfile.write(commandoutput.result) 
                            outputfile.write("\n")
                            outputfile.write("*"*40)
                            outputfile.write("\n")
                            
        ssh_session.close()
        return(True)
    except IndexError:
        return(None)
    except Exception as e:
        print(f"Error on Device {hostname}\n{e}\n")
        return(None)
