from tcpping import tcpping
import ipaddress
from multiprocessing.dummy import Pool as ThreadPool


def check_ip_network(ip_net):
    '''tests if IP-Network is an valid'''
    try:
        ipaddress.IPv4Network(ip_net)
        return (True)
    except:
        return (False)






