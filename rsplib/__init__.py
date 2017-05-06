import json, os
import requests
from enum import Enum
import datetime, time

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

def deploy(experiment, stream_running=True):
    engine = RSPClient(experiment.engine()['host'], experiment.engine()['port']);
    #if(not stream_running):
        #TODO start streams on triplewave host
    engine = RSPClient(experiment.engine()['host'], experiment.engine()['port']);
    
    execution = ExperimentExecution(experiment)
    execution.set_engine(engine.engine())

    for d in experiment.graphs():
            print("Registering static sources: " + d.location)
            execution.add_graph(engine.register_graph( d.name, d.location, d.serialization, d.default ))

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
    
    return execution

def now():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

def execute(execution, stream_running=True, collect=False):
    
    engine = RSPClient(execution.experiment.engine()['host'], execution.experiment.engine()['port']);
        
    
    execution.set_start(now())
    
    #print(experiment_execution)
    #report=json.dumps(experiment_execution, indent=4, sort_keys=True)

    if(collect):
       _spawn_collectors(tobserve, experiment, report)
    
    unit = execution.experiment.duration()["unit"]
    amount = execution.experiment.duration()["time"]
    
    intervals = [
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
        ]

    for i in intervals:
        if (unit == i[0]):
            amount = amount * i[1]
    
    end = datetime.datetime.fromtimestamp(time.time()+amount).strftime('%Y-%m-%d %H:%M:%S')
    
    print("Experiment will terminate at "+str(end))
    time.sleep(amount)
    print("Closing Up"+ str(datetime.datetime.fromtimestamp(time.time()+amount).strftime('%Y-%m-%d %H:%M:%S')))
    
    for q in engine.queries():
        for o in engine.observers(q["id"]):
            engine.unregister_observer(q["id"], o["id"])
        engine.unregister_query(q["id"])
    for s in engine.streams():
        engine.unregister_stream(s["streamURL"])
    
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

class PatternType(Enum):
    WINDOW = "WINDOW"
    GRAPH  = "GRAPH"
    STREAM = "STREAM"

class Window(object):

    def __init__(self, omega, beta, stream):
        self.range  = omega
        self.step   = beta
        self.stream = stream

    def __dict__(self):
        return {"range": str(self.range), "step":str(self.step)};

    def __str__(self):
        return self.__dict__().__str__();

    def __repr__(self):
        return self.__str__()

class Stream(object):

    def __init__(self, name, sgraph_location, scale_factor, query):
        self.query=query
        self.name=name
        self.location=sgraph_location
        self.scale_factor=scale_factor
        self.window=None

    def sgraph(self):
        return requests.get(self.location).json()

    def add_window(self, w, b):
        self.window = Window(w, b, self)
        return self.window

    def range(self):
        return self.window.range 

    def step(self):
        return self.window.step

    def __dict__(self):
        return { "name":self.name, "location":self.location, "scale_factor":self.scale_factor, 
                "window":{"range":self.window.range, "step":self.window.step }}

    def __str__(self):
        return self.__dict__().__str__()

    def __repr__(self):
        return self.__str__()

class Graph(object):

    def __init__(self, name, location, serialization, default, query):
        self.name=name
        self.location=location
        self.default=default
        self.serialization=serialization
        self.query=query

    def __dict__(self):
        return {"name":self.name, "location":self.location, "default":self.default, "serialization":self.serialization }

    def __str__(self):
        return self.__dict__().__str__()
    
    def __repr__(self):
        return self.__str__()
    
class Where(object):
    
    def __init__(self, default, query):
        self.query   = query
        self.default = [default]
        self.unnamed = []
        self.named   = []
    
    def add_default(self, default):
        self.default.append(default)
        return self

    def add_named(self, ptype, name, pattern):
        self.named.append({"type":ptype, "name":name, "pattern":pattern})
        return self
    
    def add_named_graph(self, name, pattern):
        if("?" in name): 
            return self._add_var_named_graph(name, pattern)
        else:
            return self._add_uri_named_graph(name, pattern)
            
    def _add_uri_named_graph(self, name, pattern):
        self.named.append({"type":PatternType.GRAPH, "name":name, "pattern":pattern})
        return next(filter(lambda s: s.name==name, self.query.graphs))
    
    def _add_var_named_graph(self, var, pattern):
        self.named.append({"type":PatternType.GRAPH, "name":var, "pattern":pattern})
        return self
    
    def add_named_window(self, name, pattern):
        self.named.append({"type":PatternType.WINDOW, "name":name, "pattern":pattern})
        return self
    
    def add_named_stream(self, name, pattern):
        self.named.append({"type":PatternType.STREAM, "name":name, "pattern":pattern})
        return next(filter(lambda s: s.name==name, self.query.streams))
   
    def add_unnamed(self, ptype, pattern):
        self.unnamed.append({"type":ptype, "pattern":pattern})
        return self
    
    def add_graph(self, pattern):
        self.unnamed.append({"type":PatternType.GRAPH, "pattern":pattern})
        return self
    
    def add_window(self, pattern):
        self.unnamed.append({"type":PatternType.WINDOW, "pattern":pattern})
        return self
        
    def add_stream(self, pattern):
        self.unnamed.append({"type":PatternType.STREAM, "pattern":pattern})
        return self
 
    def get_query():
        return self.query
    
    def set_group_by(self,*args):
        var_list = ""
        for a in args:
            var_list+=a
            
        self.group_by = var_list
       
    def set_having(self,having):
        self.having = having

class Query(object):

    def __init__(self,name, query_type, dialect):
        self.select_clause= ""
        self.where_clause= None
        self.query_type = query_type
        self.name= name
        self.streams = []
        self.graphs = [] 
        self.dialect=dialect
        self.prefixes = {}

    def set_select_clause(self,select):
        self.select_clause = select
    
    def set_where_clause(self, where):
        self.where_clause = Where(where, self)
        return self.where_clause
    
    def add_stream(self, name, location, scale=1):
        s = Stream(name, location, scale, self)
        self.streams.append(s)
        self.experiment._add_to_stream_set(s)
        return s

    def add_windowed_stream(self, name, location, omega, beta, scale=1):
        s = Stream(name, location, scale, self)
        s.add_window(omega, beta)
        self.streams.append(s)
        self.experiment._add_to_stream_set(s)
        return self
    
    def add_graph(self, name, location, serialization, default="false"):
        g = Graph(name, location, serialization, default, self)
        self.graphs.append(g)
        self.experiment._add_to_graphs(g)
        return g
    
    def get_stream(self, name):
        return next(filter(lambda s:s.name==name, self.streams))
 
    def _to_string_csparql(self):
        query = ""
  
        for key,value in self.prefixes.items():
            prefixQuery = "PREFIX "+ key +":<"+value+"> "
            query+=prefixQuery
        
            
        if(self.query_type=="query"):
            query += "SELECT "
        else:
            query += "CONSTRUCT "
        
        query+=self.select_clause       
        for s in self.streams:
            streamQuery = " FROM STREAM <"+s.name+"> [RANGE "+str(s.range())+" STEP "+ str(s.step())+"]\n"
            query+=streamQuery
        
        for d in self.graphs:
            named=""
            if (d.default=="false"):
                name="NAMED"
            graphQuery = "FROM "+named+" <"+d.name+">\n"
            
        query+="WHERE {"
        
        where = self.where_clause
        
        for d in where.default:
            query+= d + "\n"
        
        for u in where.unnamed:
            stringQuery = "{" + u["pattern"] + "}\n"
            query+=stringQuery
                                                            
        for u in where.named:
            if(u["type"] == PatternType.STREAM):
                raise SyntaxError("Syntax Error")
            
            if(not("?" in u["name"])):
                name = " <"+u["name"]+"> "
            else:
                name = u["name"] 
            stringQuery = PatternType.GRAPH.value + " " + name +"\n {" + u["pattern"] + "}\n"
            query+= stringQuery
     
        query+="}"
        
        return query
    
    def _to_string_cqels(self):
        query=""
        
        if(self.query_type=="query"):
            query += "SELECT "
        else:
            query += "CONSTRUCT "
        
        query+=self.select_clause +"\n"
        
        for d in self.graphs:
            named=""
            if (d.default=="false"):
                named="NAMED"
            graphQuery = "FROM "+named+" <"+d.name+">\n"
            query+=graphQuery
            
        query+="where { "
        
        where = self.where_clause
        
        for d in where.default:
            query+= d + "\n"
        
        for u in where.unnamed:
            stringQuery = "{" + u["pattern"] + "}\n"
            query+=stringQuery
                                                            
        for u in where.named:
            win=""
            if(u["type"] == PatternType.STREAM):
                s = self.get_stream(u["name"])
                win = "[range " + str(s.range())
                if(s.step()!='0'):
                    win+= " slide " + s.step()
                win+= "]\n"
            if(not("?" in u["name"])):
                name = " <"+u["name"]+"> "
            else:
                name = u["name"] 

            stringQuery = u["type"].value + " " + name + " "  + win + "{" + u["pattern"] + "}\n"
            query+= stringQuery
     
        query+="} "
        
        if(where.group_by!=None):
            query+="\ngroup by "+where.group_by
        

        if(where.having!=None):
            query+="\nhaving "+where.having

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
    
    def add_prefix(self,key,value):
        self.prefixes[key]=value
        

class Experiment(object):

    def __init__(self,  *args):
        if(len(args)==0):
            self.experiment={
                "metadata" : {},
                "queries"  : [],
                "streams"  : [],
                "graphs" : [],
                "engine"   : {},
                "duration": {}
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
    
    def duration(self):
        return self.experiment['duration']

    def _add_to_query_set(self, q):
        self.experiment['queries'].append(q)

    def _add_to_stream_set(self, s):
        self.experiment['streams'].append(s)

    def _add_to_graphs(self, d):
        self.experiment['graphs'].append(d)
        
    def set_duration(self, time, unit):
        self.experiment["duration"] =  {"time":time, "unit":unit}
        return self

    def add_engine(self, host, port,d):
        self.experiment['engine']={"host":host, "port":port, "dialect": d.name}
        return self

    def add_query(self, name, qtype="Construct", dialect=Dialects.CSPARQL):
        q = Query(name, qtype, dialect);
        q.set_experiment(self)
        self._add_to_query_set(q)
        return q
    
    def get_query(self, name):
        return next(filter(lambda q: q.name==name, self.experiment['queries']))
        
    def add_stream(self, query, name, location, scale=1):
        q = self.get_query(query)
        if(q):
            s = Stream(name, location, scale, q)
            q.streams.append(s)
            self._add_to_stream_set(s)
        return s

    def add_windowed_stream(self, query, name, location, omega, beta, scale=1):
        q = self.get_query(query)
        if(q):
            s = Stream(name, location, scale, q)
            s.add_window(omega, beta)
            q.streams.append(s)
            self._add_to_stream_set(s)
        return self    
    
    def add_graph(self, query, name, location, serialization, default="true"):
        q = self.get_query(query)
        if(q):
            d = Graph(name, location, serialization, default, q)
            q.graphs.append(d)
            self._add_to_graphs(d)
        return d
    
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
    
    def set_start(self, start_time):
        self.experiment_execution['start_time']=start_time
    
    def set_end(self, end_time):
         self.experiment_execution['end_time']=end_time

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

    def register_query(self, qname, qtype, body):  
        data = { 'queryBody': "REGISTER " + qtype.upper() + " " + qname + " AS " + body }
        print(data)
        r = requests.post(self.base+"/queries/" + qname, data = data, headers=default_headers);
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