'''This should parse the Raw-Output with Cisco Genie'''

def get_nos_fromdb(devices,hostname):
    ''' returns the hosttype of an host from DB-Devices'''
    for device in devices:
        if hostname in device["hostname"]:
            return device["type"]
    return ()

def convert_dbnos_genienos(nos):
    ''' returns hosttype like genie needs it'''
    if nos == "asa":
        return ("ASA")
    elif nos == "ios-xe":
        return ("IOSXE")
    elif nos == "cisco_ios":
        return ("IOS")
    elif nos == "cisco_nxos_ssh":
        return ("NXOS")
    else:
        return ("NO-GENIE")


def genie_parse(raw_command, raw_output, genie_nos):
    pass