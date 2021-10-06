import pickle
import dash
import dash_cytoscape as cyto
import dash_html_components as html

Data_Dump = pickle.load(open("dump_data.pickle", "rb"))

max_links=0
nodes = []
links = []
node_elements = []
edge_elements = []
root_node = ""

k = Data_Dump.keys()
if "show_cdp_neighbors_detail" in k:
    CDPs = Data_Dump["show_cdp_neighbors_detail"]
else:
    CDPs = []

if CDPs == []:
    print ("No Data Found")
    exit

def make_link_id(link):
    id = f"{link['from']}-{link['to']}_{link['local_port']}-{link['remote_port']}"
    return(id)

def make_reverse_link_id(link):
    id = f"{link['to']}-{link['from']}_{link['remote_port']}-{link['local_port']}"
    return(id)

def short_portname(port):
    if "GigabitEthernet" in port:
        newport = port.replace("GigabitEthernet", "Gi")
    elif "FastEthernet" in port:
        newport = port.replace("FastEthernet", "Fa")
    elif "FortyGigabitEthernet" in port:
        newport = port.replace("FortyGigabitEthernet", "Fo")
    elif "HundredGigE" in port:
        newport = port.replace("HundredGigE", "Hu")
    elif "TenGigabitEthernet" in port:
        newport = port.replace("TenGigabitEthernet", "Te")
    elif "TwentyFiveGigE" in port:
        newport = port.replace("TwentyFiveGigE", "Twe")
    elif "TwoGigabitEthernet" in port:
        newport = port.replace("TwoGigabitEthernet", "Two")
    elif "FiveGigabitEthernet" in port:
        newport = port.replace("FiveGigabitEthernet", "Fi")
    elif "FourHundredGigE" in port:
        newport = port.replace("FourHundredGigE", "400G")
    elif "Ethernet" in port:
        newport = port.replace("Ethernet", "Eth")
    else:
        newport = port
    return (newport)


for line in CDPs:
    host_exist = False
    link_exist = False
    link = {}
    node = {}
    try:
        node["id"]=line['destination_host'].split(".")[0]
    except KeyError:
        continue
    node["type"]=line['capabilities'].split(" ")[0] 
    link["from"]=line['Devicename']
    link["to"]=line['destination_host'].split(".")[0]
    link["local_port"]=short_portname(line["local_port"])
    link["remote_port"]=short_portname( line["remote_port"])
    links.append(link)
    for existing_node in nodes:  # check if node allready exist
        if node["id"] == existing_node["id"]:
            host_exist = True
    if not host_exist:
        nodes.append(node)
  
for node in nodes:
    node_element = {'data':{'id':node['id'],'label':node['id']},
                    'classes':node['type']}
    node_elements.append(node_element)
for link in links:
    link_element = {'data':{'id':f"Link_{make_link_id(link)}",'source':link["from"],'target':link["to"],'key':f"{make_link_id(link)}","classes": "bezier","local_port":link["local_port"],"remote_port":link["remote_port"]}}
    revers_element = {'data':{'id':f"Link_{make_reverse_link_id(link)}",'source':link["to"],'target':link["from"],'key':f"{make_reverse_link_id(link)}","classes": "bezier","local_port":link["remote_port"],"remote_port":link["local_port"]}}
    if revers_element in node_elements:
        continue
    node_elements.append(link_element)

for node in nodes: # find node with max links
    number_of_links = 0
    for link in links:
        if node["id"] == link["from"] or node["id"] == link["to"]:
            number_of_links += 1
        if number_of_links > max_links:
            root_node = node
            max_links = number_of_links

root_node = f"'[ id = {root_node}]'"

cyto_elements = node_elements

print("*"*40)
print(root_node)
print(node_elements)

app = dash.Dash(__name__)
app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape',
        elements=cyto_elements,
        layout={'name': 'breadthfirst','root':'[id ]'},
        style={'width': '100%', 'height': '1000px'},
        stylesheet=[
            {'selector': 'node',
            'style': {
            'label': 'data(id)'}},
            {'selector': 'Link',
            'style': {
                "text-background-color": "white",
                "text-background-opacity": 1,
                "text-background-shape": "round-rectangle",
                'curve-style': 'bezier',
                'line-color': 'gray',
                'source-label':'data(local_port)',
                'target-label':'data(remote_port)',
                "source-text-offset": "100px",
                "target-text-offset": "100px",
                "source-text-rotation": "autorotate",
		        "target-text-rotation": "autorotate",}},
            {'selector': '.Host',
             'style':{
                 'shape':'square',
                 'background-image':['./assets/sq_laptop.svg'],
                 'background-opacity': 0,
                 'background-fit': 'contain',
                 'background-clip': 'none',
                 'width': '100px',
                 'height': '100px'}},
            {'selector': '.Router',
             'style':{
                 'background-image':['./assets/c_router.svg'],
                 'background-opacity': 0,
                 'background-fit': 'contain',
                 'background-clip': 'none',
                 'width': '100px',
                 'height': '100px'
            }},
            {'selector': '.Switch',
            'style':{
                 'shape':'square',
                 'background-image':['./assets/sq_switch.svg'],
                 'background-opacity': 0,
                 'background-fit': 'contain',
                 'background-clip': 'none',
                 'width': '100px',
                 'height': '100px'
             }},
            ]
    )])


if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0")