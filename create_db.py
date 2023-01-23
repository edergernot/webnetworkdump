from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask (__name__)
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dump_db.sqlite3'
app.config ['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
class network_device(db.Model):
   id = db.Column('device_id', db.Integer, primary_key = True)
   device_name = db.Column(db.String(100))
   device_ip = db.Column(db.String(100))  
   device_username = db.Column(db.String(100))
   device_password = db.Column(db.String(100))
   device_type = db.Column(db.String(50))
   device_enabled = db.Column(db.Boolean())

def __init__(self, device_name, device_ip, device_username,device_password,device_type,device_enabled):
    self.device_name = device_name
    self.device_ip = device_ip
    self.device_username = device_username
    self.device_password = device_password
    self.device_type = device_type
    self.device_enabled = device_enabled

class mac_address(db.Model):
   id = db.Column('mac_id', db.Integer, primary_key = True)
   mac_address = db.Column(db.String(50))
   device_name = db.Column(db.String(100))
   device_port = db.Column(db.String(100))
   port_vlan = db.Column(db.String(100))
   mac_type = db.Column(db.String(100))

def __init__(self, mac_address, device_name, device_port, port_vlan, mac_type):
   self.mac_address = mac_address
   self.device_name = device_name
   self.device_port = device_port
   self.port_vlan = port_vlan
   self.mac_type = mac_type
   
@app.cli.command()
def __init__(self):
   db.create_all()
