import json, os
import requests
from enum import Enum
import datetime, time
    
default_headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Access-Control-Allow-Origin': '*'
        }
        
class RSPSource(object):

    def __init__(self, endpoint, port):
        self.endpoint = endpoint;
        self.port = port;
        self.base = self.endpoint+":"+str(self.port);

    def _result(self, resp):
        return resp.json();
   
    def name(self):
        return self.sgraph()['sld:streamName']

    def location(self):
        return self.sgraph()['sld:streamLocation']
   
    def tbox(self):
        return self.sgraph()['sld:tBoxLocation']

    def _observer(self, q, o, spec):
        if(req['type'] == 'ws'):
            print("websocket observer") 
        else:
            print("http observer")
        return self._result(resp)

    def description(self):
        return self.base+"/sgraph"
    
    def sgraph(self):
        r = requests.get(self.base+"/sgraph")
        return self._result(r);

    def start(self):
        r = requests.get(self.base+"/start")
        return self._result(r);


class RSPHub(object):

    def __init__(self, endpoint, port):
        self.endpoint = endpoint;
        self.port = port;
        self.base = self.endpoint+":"+str(self.port);