import json, os, requests, datetime, time, uuid, threading
from rsplib.processing.consumer.query import Query, Dialects, Stream, Graph, Where, Window

def open_remote(url):
    e = requests.get(url).json()
    return Experiment(e)

def open_file(path):
    with open(path) as input_file:    
        return Experiment(json.load(input_file))

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
            self.experiment={
                "metadata" : {},
                "queries"  : [],
                "streams"  : [],
                "graphs" : [],
                "engine"   : {},
                "duration": {}
            }
            exp = args[0]
            for q in exp['queries']:
                query = Query(q['name'], q['type'], Dialects(q['dialect']))
                
                if("select_clause" in exp):
                    query.set_select_clause(q['select_clause'])
                if("select_clause" in exp):
                    query.set_construct_clause(q['construct_clause'])
                if("having" in exp):
                    query.set_having(q['having'])
                if("order_by" in exp):
                    query._set_order_by(q['order_by'])
                if("group_by" in exp):
                    query._set_group_by(q['group_by'])
              
                for s in q['streams']:
                    stream = query.add_windowed_stream(s['name'], 
                                                       s['sgraph_location'],
                                                       s['window']['range'], 
                                                       s['window']['step'], 
                                                       s['scale_factor'])
                    
                    self.experiments['streams'].append(stream)
                    
                for g in q['graphs']:
                    graph = query.add_graph(g['name'], 
                                            g['location'], 
                                            g['serialization'], 
                                            g['default'])
                    self.experiments['graphs'].append(graph)
                    
                default = q["where_clause"]['default']
                
                where = Where(query, default[0])
                
                for _def in default[1:]:
                    where.add_default(_def)
                
                for n in q["where_clause"]['named']:
                    where.add_named(n['type'], n['name'], n['pattern'])
                
                for u in q["where_clause"]['unnamed']:
                    where.add_named(u['type'], u['pattern'])
                
                query.where_clause = where 
                
                self.experiments['queries'].append(query)

                for s in exp['streams']:
                    
                    stream = self.experiment.add_windowed_stream(s['name'], 
                                                       s['sgraph_location'],
                                                       s['window']['range'], 
                                                       s['window']['step'], 
                                                       s['scale_factor'])
                    
                for g in exp['graphs']:
                    graph = query.add_graph(g['name'], 
                                            g['location'], 
                                            g['serialization'], 
                                            g['default'])
                    self.experiments['graphs'].append(graph)
                    
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
        return self
    
    def __str__(self):
        return self.experiment.__str__()
    
    def __dict__(self):
        return dict(self.experiment)

    def jsonld(self):
        context =  {
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "rsplab": "http://rsp-lab.org/ontology/",
            "engine": { "@id":"rsplab:engine", "@container":"@index","@type": "rsplab:RSPEngine"},
            "streams": { "@id":"rsplab:stream", "@container": "@index","@type":"rsplab:RDFStream"},
            "queries": { "@id":"rsplab:query", "@container": "@index"},
            "dataset": { "@id":"rsplab:dataset", "@container": "@index", "@type":"rsplab:Dataset"},
            "port":  { "@id":"rsplab:port", "@type":"xsd:integer"},
            "dialect":  { "@id":"rsplab:dialect", "@type":"xsd:string"},
            "location":  { "@id":"rsplab:location", "@type":"@id"},
            "host":  { "@id":"rsplab:location", "@type":"@id"},
            "default":{"@id":"rsplab:default","@type":"xsd:boolean"},
            "name":{"@id":"rsplab:name","@type":"xsd:string"},
            "serialization":{"@id":"rsplab:serialization","@type":"xsd:string"},
            "scale_factor": {"@id":"rsplab:scalefactor","@type":"xsd:integer"},
            "window": {"@id":"rsplab:window","@type":"xsd:string"},
            "range": {"@id":"rsplab:range","@type":"xsd:dateTime"},
            "step": {"@id":"rsplab:step","@type":"xsd:dateTime"},
            "duration": {"@id":"rsplab:step","@type":"xsd:dateTime"}}

        exp = dict(self.experiment)

        metadata = exp.pop('metadata', None)

        exp["@context"] = context;
        exp["duration"] = metadata['duration']
        exp["@type"] = "rsplab:Experiment"
        exp["@id"] = "http://rsp-lab.org/"+metadata["uuid"] 

        return json.dumps(e, default=exp, indent=4, sort_keys=True)

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
    
class Report(object):
    def __init__(self, uuid, title, descr, extension="n3"):
        self.report_template = Template(open("./templates/"+extension+"/report.tmpl").read())
        self.report_path = str(uuid)+"."+extension
        with open(self.report_path, "w+") as report_file:
            report_file.write(self.report_template.substitute(
                {"experiment":uuid, 
                 "title":title,
                 "description":descr,
                 "date":self.now(),
                 "subsets":"    \n $licence"}))
        report_file.close()

        self.subsets = []
        self.results = []

    def now(self):
        return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

    def _append(self, collection, exp_uuid, templ_map, exp_template):
        with open(self.report_path, "a") as report_file:
            report_file.write("\n")
            report_file.write(exp_template.substitute(templ_map)+"\n")
            collection.append(exp_uuid)
        report_file.close()

    def add_default_licence(self):
        licence = open("./templates/n3/licence.tmpl").read()
        template = Template(open(self.report_path).read())
        with open(self.report_path, "w+") as report_file:
            report_file.write(template.substitute(
                {"licence":licence+"\n",
                 "results":"$results"}))
        report_file.close()

    def add_experiment(self, exp_uuid, name, uri):
        exp_template = Template(open("./templates/n3/experiment.tmpl").read())
        templ_map = {
         "description":exp_uuid,
         "title": name, 
         "experiment_description_json":uri}
        self._append(self.subsets, exp_uuid, templ_map, exp_template)

    def add_cpu(self, exp_uuid, name, duration, uri):
        exp_template = Template(open("./templates/n3/cpu.tmpl").read())
        templ_map = {
         "cpu_load":exp_uuid,
         "title": name, 
         "cpu_load_dump":uri,
         "duration":duration}
        self._append(self.subsets, exp_uuid, templ_map, exp_template)

    def add_memory(self, exp_uuid, name, duration, uri):
        exp_template = Template(open("./templates/n3/memory.tmpl").read())
        templ_map = {
         "memory_load":exp_uuid,
         "title": name, 
         "memory_load_dump":uri,
         "duration":duration}
        self._append(self.subsets, exp_uuid, templ_map, exp_template)

    def add_result(self, exp_uuid, name, query, body, uri):
        exp_template = Template(open("./templates/n3/result.tmpl").read())
        templ_map = {
         "queryname_results":exp_uuid,
         "title": name,
         "querybody":body, 
         "queryname_dump_uri":uri,
         "queryname":query
        }
        
        self._append(self.results, exp_uuid, templ_map, exp_template)

    def add_results(self, exp_uuid, name, dialect, queries):
        exp_template = Template(open("./templates/n3/results.tmpl").read())
        templ_map = {
         "query_results":exp_uuid,
         "title": name, 
         "dialect":dialect,
         "queries":queries,
         "results":"$results"
         }

        self._append(self.subsets, exp_uuid, templ_map, exp_template)

    def _n3(self, exp_uuid):
        template = Template(open(self.report_path).read())

        with open(exp_uuid+".n3", "w") as report_file:
            subset_string=""
            result_string=""
            for subset in self.subsets:
                subset_string+=";\n    void:subset :"+subset
            for res in self.results:
                result_string+=";\n    void:subset :"+res
            
            subset_string+=".\n"
            result_string+=".\n"

            templ_map = {"subsets":subset_string, "results":result_string}
            report_file.write(template.substitute(templ_map)+"\n")
            report_file.close()

    def _nt(self, exp_uuid):
        self._n3(exp_uuid)

        testrdf = open(exp_uuid+".n3").read()
        g =Graph().parse(data=testrdf, format='n3')

        with open(exp_uuid+".nt", "w+") as jsonfile:
            jsonfile.write(g.serialize(format='nt'))
        jsonfile.close()

    def _trig(self, exp_uuid):
        self._n3(exp_uuid)

        testrdf = open(exp_uuid+".n3").read()
        g =Graph().parse(data=testrdf, format='n3')

        with open(exp_uuid+".trig", "w+") as jsonfile:
            jsonfile.write(g.serialize(format='trig'))
        jsonfile.close()

    def _rdf(self, exp_uuid):
        self._n3(exp_uuid)

        testrdf = open(exp_uuid+".n3").read()
        g =Graph().parse(data=testrdf, format='n3')

        with open(exp_uuid+".rdf", "w+") as jsonfile:
            jsonfile.write(g.serialize(format='xml'))
        jsonfile.close()

    def _jsonld(self, exp_uuid):
        self._n3(exp_uuid)

        testrdf = open(exp_uuid+".n3").read()
        g =Graph().parse(data=testrdf, format='n3')

        context = {
            "dbpedia": "http://dbpedia.org/resource/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "owl": "http://www.w3.org/2002/07/owl#",
            "prov": "http://www.w3.org/ns/prov#",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "rsplab": "http://rsp-lab.org/ontology/",
            "sd": "http://www.w3.org/ns/sparql-service-description#",
            "void": "http://rdfs.org/ns/void#",
            "wv": "http://vocab.org/waiver/terms/norms",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
        }

        with open(exp_uuid+".json-ld", "w+") as jsonfile:
            jsonfile.write(g.serialize(format='json-ld', indent=4, context=context))
        jsonfile.close()

    def serialize(self, exp_uuid, extension="n3"):
        {"n3":self._n3,
         "json-ld":self._jsonld,
         "nt":self._nt,
         "rdf":self._rdf,
         "trig":self._trig
        }[extension](exp_uuid)


