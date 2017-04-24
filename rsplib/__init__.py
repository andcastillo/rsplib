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
    
    engine = RSPClient(experiment.engine()['host'], experiment.engine()['port']);
    
    execution = ExperimentExecution(experiment)
    execution.set_engine(engine.engine())

    for d in experiment.graphs():
            print("Registering static sources: " + d.name)
            execution.add_graph(engine.register_graph( d.name, d.location, d.serialization, d.default ))
            
    #if(not stream_running):
        #TODO start streams on triplewave host

    for s in experiment.stream_set():
            print ("Registering stream: " + s.name)
            execution.add_stream(engine.register_stream( s.name, s.location ))

    for q in experiment.query_set():
        print("Registering query " + q.name +" ")
        for i in range(0,1):
            print(engine.register_query(q.name, q.query_type, q.query_body()))
            print("Registering observers for "+q.name)
            ro = engine.new_observer(q.name, "default", {"host":"csparql.westeurope.cloudapp.azure.com","type":"ws","port":9101,"name":"default"}); 
            execution.add_observer({q.name:ro})
            execution.add_queries(engine.queries());
    
    #print(experiment_execution)
    #report=json.dumps(experiment_execution, indent=4, sort_keys=True)

    if(collect):
       _spawn_collectors(tobserve, experiment, report)

    return execution
#end


class Dialects(Enum):
    CSPARQL = "C-SPARQL"
    CQELS   = "CQELS"
    RSPQL   = "RSPQL"
    RSEPQL  = "RSEPQL"

class QueryType(Enum):
    CONSTRUCT = "CONSTRUCT"
    SELECT    = "SELECT"
    ASK       = "ASK"
    DESCRIBE  = "DESCRIBE"

class Window(object):

    def __init__(self, omega, beta):
        self.range=omega
        self.step=beta
        self.bgp=None

    def add_bgp(self,bgp):
        self.bgp=bgp
        return self

    def __dict__(self):
        return {"range": str(self.range), "step":str(self.step)};

    def __str__(self):
        return self.__dict__().__str__();

    def __repr__(self):
        return self.__str__()

class Stream(object):

    def __init__(self, name, sgraph_location, scale_factor=1):
        self.name=name
        self.location=sgraph_location
        self.scale_factor=scale_factor
        self.window=None

    def sgraph(self):
        return requests.get(self.location).json()

    def add_window(self, w, b):
        self.window = Window(w,b)
        return self.window

    def range(self):
        return self.range 

    def step(self):
        return self.step

    def __dict__(self):
        return { "name":self.name, "location":self.location, "scale_factor":self.scale_factor, 
                "window":{"range":self.window.range, "step":self.window.step }}

    def __str__(self):
        return self.__dict__().__str__()

    def __repr__(self):
        return self.__str__()

class Graph(object):

    def __init__(self, name, location, serialization, default="false"):
        self.name=name
        self.location=location
        self.default=default
        self.serialization=serialization

    def __dict__(self):
        return {"name":self.name, "location":self.location, "default":self.default, "serialization":self.serialization }

    def __str__(self):
        return self.__dict__().__str__()
    
    def __repr__(self):
        return self.__str__()
    
    

class Query(object):

    def __init__(self,name, query_type, dialect):
        self.select_clause= ""
        self.where_clause= ""
        self.query_type = query_type
        self.name= name
        self.streams = []
        self.graphs = [] 
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
    
    def add_graph(self, g, location, serialization, default):
        d = graph(g,location, serialization, default)
        self.graphs.append(d)
        self.experiment._add_to_graphs(d)
        return d
    
    def _to_string_csparql(self):
        query = ""
        if(self.query_type=="query"):
            query += "SELECT "
        else:
            query += "CONSTRUCT "
        
        query+=self.select_clause        
        for s in self.streams:
            streamQuery = " FROM STREAM <"+s.name+"> [RANGE "+str(s.range)+" STEP "+ str(s.step)+"]\n"
            query+=streamQuery
        
        for d in self.graphs:
            graphQuery = "FROM <"+d.location+">\n"
            query+=graphQuery
            
        query+="\nWHERE "
        query+=self.where_clause
        return query
    
    def _to_string_cqels(self):
        query=""
        return query

    def query_body(self):
        return {Dialects.CSPARQL: self._to_string_csparql, 
                 Dialects.CQELS: self._to_string_cqels }[self.dialect]().__str__()

    def __dict__(self):
        body = { Dialects.CSPARQL: self._to_string_csparql, 
                 Dialects.CQELS: self._to_string_cqels }[self.dialect]().__str__()
        return {"name":self.name, "body": body, "type": self.query_type, "dialect":self.dialect.name}

    def __str__(self):
        return self.__dict__().__str__()
        
    def __repr__(self):
        return self.__str__()
    
    def set_experiment(self, e):
        self.experiment = e

class Experiment(object):

    def __init__(self,  *args):
        if(len(args)==0):
            self.experiment={
                "metadata" : {},
                "queries"  : [],
                "streams"  : [],
                "graphs" : [],
                "engine"   : {}
            }
        else:
            self.experiment=args[0]
            if(not('queries' in self.experiment )):
                self.experiment['queries'] = []
            if(not('streams' in self.experiment )):
                self.experiment['streams'] = []
            if(not('graphs' in self.experiment )):
                self.experiment['graphs'] = []

    def metadata(self):
        return self.experiment['metadata']

    def engine(self):
        return self.experiment['engine']

    def stream_set(self):
        return self.experiment['streams']

    def query_set(self):
        return self.experiment['queries']

    def graphs(self):
        return self.experiment['graphs']

    def _add_to_query_set(self, q):
        self.experiment['queries'].append(q)

    def _add_to_stream_set(self, s):
        self.experiment['streams'].append(s)

    def _add_to_graphs(self, d):
        self.experiment['graphs'].append(d)

    def add_engine(self, host, port,d):
        self.experiment['engine']={"host":host, "port":port, "dialect": d.name}
        return self

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
        return None
        
        
    def add_stream(self, query, name, location):
        q = self.get_query(query)
        if(q):
            s = Stream(name, location)
            q.streams.append(s)
            self._add_to_stream_set(s)
        return s

    def add_windowed_stream(self, query, name, location, omega, beta):
        q = self.get_query(query)
        if(q):
            s = Stream(name, location)
            s.add_window(omega, beta)
            q.streams.append(s)
            self._add_to_stream_set(s)
        return self    
    
    def add_graph(self, query, g, location, serialization, default):
        q = self.get_query(query)
        if(q):
            d = Graph(g,location, serialization, default)
            q.graphs.append(d)
            self._add_to_graphs(d)
        return self
    
    def __str__(self):
        return self.experiment.__str__()
    
    def __dict__(self):
        return self.experiment
        

class ExperimentExecution(object):
    
    def __init__(self, origin):
        self.experiment_execution={}
        self.experiment= origin
        
        self.experiment_execution['D'] = []
        self.experiment_execution['S'] = []
        self.experiment_execution['Q'] = []
        self.experiment_execution['O'] = []
        self.experiment_execution['K'] = None # save the KPIs
        self.experiment_execution['R'] = None # save the result location
       
    def set_engine(self, engine):
        self.experiment_execution['E'] = engine
        root = self.experiment_execution['E']['runUUID']
        if not os.path.exists(root):
                os.makedirs(root)

    def add_graph(self, d):
         self.experiment_execution['D'].append(d)
    
    def add_stream(self, s):
         self.experiment_execution['S'].append(s)
    
    def add_query(self, q):
         self.experiment_execution['Q'].append(q)
    
    def add_queries(self, ql):
        for q in ql:
             self.add_query(q)
    
    def add_observer(self, o):
        self.experiment_execution['O'].append(o)
        
    def __dict__(self):
        return {'Experiment': self.experiment.__dict__(),
                           'Execution': self.experiment_execution }
    
            
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
        print(resp.text)
        return resp.json();

    def _observer(self, q, o, spec):
        if(req['type'] == 'ws'):
            print("websocket observer") 
        else:
            print("http observer")
        return self._result(resp)

    def graphs(self):
        r = requests.get(self.base+"/datasets")
        print (r._content())
        return self._result(r);

    def graph(self, s):
        r = requests.get(self.base+"/datasets/" + s)
        return self._result(r);

    def register_graph(self, graph_name, graph_uri, graph_serialization="RDF/XML", default=False):
        data = { "location": graph_uri, "name": graph_name, "isDefault": default, "serialization": graph_serialization }
        r = requests.post(self.base+"/datasets/"+graph_name, data = data, headers=default_headers);
        return self._result(r);

    def unregister_graph(self, s):
        r = requests.delete(self.base+"/datasets/"+s);
        return self._result(r);

    def streams(self):
        r = requests.get(self.base+"/streams")
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