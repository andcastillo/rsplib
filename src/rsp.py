import json, os
import requests
from enum import Enum

def open_remote(url):
    e = requests.get(url).json()
    return Experiment(e)

def open_file(path):
    with open(path) as input_file:    
        return Experiment(json.load(input_file))


def _record(p, i):
    experiment_execution[p] = i

def _spawn_collectors(tobserve,experiment,report):
    for (q,ro) in tobserve:
            client.containers.run("rspsink", name=ro['id']+"_collector", 
                auto_remove=True,
                command=[ro['observer']['dataPath'], q['name'], "./data/"+root+"/"+q["result_path"]+ro['id']+"/", str(experiment['metadata']['duration']), report],
                volumes={'resultsdata': {'bind': '/usr/src/app/data', 'mode': 'rw'}}, 
                detach=True)

def execute(experiment, stream_running=True, collect=False):
    
    engine = RSPClient(experiment['engine']['host'], experiment['engine']['port']);

    experiment_execution['Origin'] = experiment
    experiment_execution['E'] = client.engine()
    experiment_execution['D'] = []
    experiment_execution['S'] = None
    experiment_execution['Q'] = []
    experiment_execution['K'] = None # save the KPIs
    experiment_execution['R'] = None # save the result location

    root = experiment_execution['E']['runUUID']

    if not os.path.exists(root):
                os.makedirs(root)

    datasets=[]
    for d in experiment['datasets']:
            print "Registering dataset: " + str(d['name'])
            datasets.append(rsp.register_dataset( d['name'], d['location'], d['serialization'], d['default'] ))

    _record('D', datasets)

    streams=[]

    #if(not stream_running):
        #TODO start streams on triplewave host

    for s in experiment['streams']:
            print "Registering stream: " + str(s['name'])
            streams.append(rsp.register_stream( s['name'], s['location'] ))

    _record('S',streams)

    for q in experiment['queries']:
        print "Registering query " + q['name'] +" "+ str(q['repeat']) + " times."
        for i in range(0,q['repeat']):
            print rsp.register_query(q['name'], q['body'])
            for o in  q['observers']:
                print "Registering observers for "+q['name']+ " : " + o['name']
                ro = rsp.new_observer(q['name'], o['name'], o);
                if o['persist']:
                    tobserve.append((q,ro));
            _record('Q', rsp.queries());

    report=json.dumps(experiment_execution, indent=4, sort_keys=True)

    if(collect):
       _spawn_collectors(tobserve, experiment, report)

    print report
#end


class Dialects(Enum):
    CSPARQL = "C-SPARQL"
    CQELS   = "CQELS"
    RSPQL   = "RSPQL"
    RSEPQL  = "RSEPQL"

class Window(object):

    def __init_(self, omega, beta):
        self.omega=omega
        self.beta=beta

class Stream(object):

    def __init__(self, name, sgraph_location, scale_factor=1):
        self.name=name;
        self.sgraph_location=sgraph_location
        self.scale_factor=scale_factor

    def sgraph(self):
        return requests.get(self.sgraph_location).json()

    def add_window(self, w, b):
        self.window = (w,b)

    def range(self):
        return str(self.window[0]) 

    def step(self):
        return str(self.window[1])

    def __str__(self):
        return {'name':self.name, 'location':self.sgraph_location, 'scale_factor':self.scale_factor}.__str__()

    def __repr__(self):
        return self.__str__()

class Dataset(object):

    def __init__(self, name, location, serialization, default=False):
        self.name=name
        self.location=location
        self.serialization=serialization
        self.default=default

    def __str__(self):
        return {'name':self.name, 'location':self.location, 'default':self.default, 'serialization':self.serialization}.__str__()

    def __repr__(self):
        return self.__str__()

class Query(object):

    def __init__(self,name, query_type, dialect):
        self.select_clause= ""
        self.where_clause= ""
        self.query_type = query_type
        self.name= name
        self.streams = []
        self.datasets = [] 
        self.dialect=dialect

    def set_select_clause(self,select):
        self.select_clause = select
    
    def set_where_clause(self,where):
        self.where_clause = where
    
    def add_stream(self, name, location):
        s = Stream(name, location)
        self.streams.append(s)
        self.experiment._add_to_stream_set(s)
        return s

    def add_windowed_stream(self, name, location, omega, beta):
        s = Stream(name, location)
        s.add_window(omega, beta)
        self.streams.append(s)
        self.experiment._add_to_stream_set(s)
        return self
    
    def add_dataset(self,dataset,location, serialization, default):
        d = Dataset(location, serialization, default)
        self.datasets.append(d)
        self.experiment._add_to_datasets(d)
        return d
    
    def _to_string_csparql(self):
        query = ""
        if(self.query_type=="query"):
            query += "SELECT "
        else:
            query += "CONSTRUCT "
        
        query+=self.select_clause        
        for s in self.streams:
            streamQuery = " FROM STREAM <"+s.name+"> [RANGE "+s.range()+" STEP "+ s.step()+"]\n"
            query+=streamQuery
        
        for d in self.datasets:
            datasetQuery = "FROM <"+d.name+">\n"
            query+=datasetQuery
            
        query+="WHERE "
        query+=self.where_clause
        return query
    
    def _to_string_cqels(self):
        query=""
        return query

    def query_body():
        return {Dialects.CSPARQL: self._to_string_csparql, 
                 Dialects.CQELS: self._to_string_cqels }[self.dialect]().__str__()

    def __str__(self):
        m = { Dialects.CSPARQL: self._to_string_csparql, 
                 Dialects.CQELS: self._to_string_cqels }[self.dialect]().__str__()
        return m
        
    def __repr__(self):
        return self.__str__()
    
    def set_experiment(self, e):
        self.experiment = e

class Experiment(object):

    def __init__(self,  *args):
        if(len(args)==0):
            self.experiment={
                'metadata' : {},
                'queries'  : [],
                'streams'  : [],
                'datasets' : [],
                'engine'   : {}
            }
        else:
            self.experiment=args[0]
            if(not('queries' in self.experiment )):
                self.experiment['queries'] = []
            if(not('streams' in self.experiment )):
                self.experiment['streams'] = []
            if(not('datasets' in self.experiment )):
                self.experiment['datasets'] = []

    def metadata(self):
        return self.experiment['metadata']

    def engine(self):
        return self.experiment['engine']

    def stream_set(self):
        return self.experiment['streams']

    def query_set(self):
        return self.experiment['queries']

    def datasets(self):
        return self.experiment['datasets']

    def _add_to_query_set(self, q):
        self.experiment['queries'].append(q)

    def _add_to_stream_set(self, s):
        self.experiment['streams'].append(s)

    def _add_to_datasets(self, d):
        self.experiment['datasets'].append(d)

    def add_engine(self, host, port,d):
        self.experiment['engine']={'host':host, 'port':port, "dialect": d}

    def add_query(self, name, qtype="Construct", dialect=Dialects.CSPARQL):
        q = Query(name, qtype, dialect);
        q.set_experiment(self)
        self._add_to_query_set(q) 
        return q

    def get_query(self, name):
        for q in self.experiment['queries']:
            if q.name==name:
                return q
        print(name+" not found")

    def __str__(self):
        return self.experiment.__str__()


default_headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Access-Control-Allow-Origin': '*'
        }

class RSPClient(object):

    def __init__(self, endpoint, port):
        self.endpoint = endpoint;
        self.port = port;
        self.base = self.endpoint+":"+str(self.port);

    def _result(self, resp):
        return resp.json();

    def _observer(self, q, o, spec):
        if(req['type'] == 'ws'):
            print("websocket observer") 
        else:
            print("http observer")
        return self._result(resp)

    def datasets(self):
        r = requests.get(self.base+"/datasets")
        print (r._content())
        return self._result(r);

    def dataset(self, s):
        r = requests.get(self.base+"/datasets/" + s)
        return self._result(r);

    def register_dataset(self, dataset_name, dataset_uri, dataset_serialization="RDF/XML", default=False):
        data = { "iri": dataset_uri, "name": dataset_name, "isDefault": default, "serialization": dataset_serialization }
        r = requests.post(self.base+"/datasets/"+stream_name, data = data, headers=default_headers);
        return self._result(r);

    def unregister_dataset(self, s):
        r = requests.delete(self.base+"/datasets/"+s);
        return self._result(r);

    def streams(self):
        r = requests.get(self.base+"/streams")
        print (r._content())
        return self._result(r);

    def stream(self, s):
        r = requests.get(self.base+"/streams/" + s)
        return self._result(r);

    def register_stream(self, stream_name, stream_URI):
        r = requests.post(self.base+"/streams/"+stream_name, data = {'streamIri': stream_URI }, headers=default_headers);
        return self._result(r);

    def unregister_stream(self, s):
        r = requests.delete(self.base+"/streams/"+s);
        return self._result(r);

    def queries(self):
        r = requests.get(self.base+"/queries");
        return self._result(r);

    def query(self, q):
        r = requests.get(self.base+"/queries/" + q);
        return self._result(r);

    def register_query(self, q, qtype, body):        
        data = { 'queryBody': "REGISTER " + qtype.upper() + " " + q + " AS " + body }
        r = requests.post(self.base+"/queries/" + q, data = data, headers=default_headers);
        return self._result(r);

    def unregister_query(self, q):
        r = requests.delete(self.base + "/queries/" + q);
        return self._result(r);

    def observers(self, q):
        r = requests.get(self.base + "/queries/" + q + "/observers");
        return self._result(r);

    def observer(self, q, o):
        r = requests.get(self.base + "/queries/" + q + "/observers/" + o);
        return self._result(r);

    def register_observer(self, q, obs_name, obs_spec ):        
        r = requests.post(self.base+"/queries/" + q + "/observers/" + obs_name, data = obs_spec, headers=default_headers);
        return self._result(r);

    def new_observer(self, q, obs_name, obs_spec):
        self.register_observer(q, obs_name, obs_spec);
        return self.observer(q, obs_name);

    def unregister_observer(self, q, o):
        r = requests.delete(self.base+"/queries/" + q + "/observers/" + o);
        return self._result(r);

    def engine(self):
        r = requests.get(self.base+"/engine")
        return self._result(r);