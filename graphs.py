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


for line in CDPs:
    host_exist = False
    link_exist = False
    link = {}
    node = {}
    node["id"]=line['destination_host'].split(".")[0]
    node["type"]=line['capabilities'].split(" ")[0] 
    link["from"]=line['Devicename']
    link["to"]=line['destination_host'].split(".")[0]
    link["local_port"]=line["local_port"]
    link["remote_port"]=line["remote_port"]
    links.append(link)
    for existing_node in nodes:  # check if node allready exist
        if node["id"] == existing_node["id"]:
            host_exist = True
    if not host_exist:
        nodes.append(node)
  
for node in nodes:
    node_element = {'data':{'id':node['id'],'label':node['type']},
                    'classes':node['type']}
    node_elements.append(node_element)
for link in links:
    link_element = {'data':{'id':f"Link_{make_link_id(link)}",'source':link["from"],'target':link["to"],'key':f"{make_link_id(link)}","classes": "bezier"}}
    revers_element = {'data':{'id':f"Link_{make_reverse_link_id(link)}",'source':link["to"],'target':link["from"],'key':f"{make_reverse_link_id(link)}","classes": "bezier"}}
    if revers_element in node_elements:
        continue
    node_elements.append(link_element)

for node in nodes: # find node with max links
    number_of_links = 0
    for link in links:
        if node == link["from"] or node == link["to"]:
            number_of_links += 1
    if number_of_links < max_links:
        root_node = node
        max_links = number_of_links

root_node = f"'[ id = {root_node}]'"

cyto_elements = node_elements

app = dash.Dash(__name__)
app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape',
        elements=cyto_elements,
        layout={'name': 'breadthfirst','root':'[id ]'},
        style={'width': '75%', 'height': '500px'},
        stylesheet=[
            {'selector': 'node',
            'style': {
            'label': 'data(id)'}},
            {'selector': 'Link',
            'style': {
                'curve-style': 'bezier',
                'line-color': 'gray'}},
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