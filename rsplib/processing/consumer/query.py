from enum import Enum

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
        
    def __dict__(self):
        return { "default": self.default, "named": self.named, "unnamed":self.unnamed }
    
    def __str__(self):
        return self.__dict__().__str__()
    
    def __repr__(self):
        return self.__str__()
    
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

class Query(object):

    def __init__(self,name, query_type, dialect):
        self.select_clause= ""
        self.construct_clause= ""
        self.where_clause= None
        self.query_type = query_type
        self.name= name
        self.streams = []
        self.graphs = [] 
        self.dialect=dialect
        self.prefixes = {}
        self.group_by=""
        self.order_by=""
        self.having=""
        
    def set_construct_clause(self, construct):
        self.construct_clause = construct
        
    def set_select_clause(self, select):
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
        return s
    
    def add_graph(self, name, location, serialization, default="false"):
        g = Graph(name, location, serialization, default, self)
        self.graphs.append(g)
        self.experiment._add_to_graphs(g)
        return g
    
    def get_stream(self, name):
        return next(filter(lambda s:s.name==name, self.streams))
    
    def add_prefix(self,key,value):
        self.prefixes[key]=value
        return self
        
    def set_group_by(self,*args):
        var_list = ""
        for a in args:
            var_list+=a
            
        self.group_by = var_list
        return self
       
    def set_having(self,having):
        self.having = having
        return self
    
    def set_order_by(self,*args):
        var_list = ""
        for a in args:
            var_list+=a
        
        self.order_by = var_list
        return self
    
    def _set_group_by(self,group_by):
        self.group_by = group_by
        return self
        
    def _set_order_by(self,order_by):
        self.order_by = order_by
        return self
        
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
        
        ## TODO order by and groupby
        
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
        
        if(self.group_by!=None):
            query+="\ngroup by "+self.group_by
        

        if(self.having!=None):
            query+="\nhaving "+self.having

        return query

    def query_body(self):
        return {Dialects.CSPARQL: self._to_string_csparql, 
                 Dialects.CQELS: self._to_string_cqels }[self.dialect]().__str__()

    def _structure(self):
        structure = {}
        if (self.prefixes!={} and self.prefixes != None):
            structure["prefixes"]=self.prefixes
        if (self.select_clause!='' and self.select_clause != None):
            structure["select_clause"]=self.select_clause
        if (self.construct_clause!='' and self.construct_clause != None):
            structure["construct_clause"]=self.construct_clause
        if (self.where_clause != None):
            structure["where_clause"]=self.where_clause
        if (self.streams!=[] and self.streams != None):
            structure["streams"]=self.streams
        if (self.graphs!=[] and self.graphs != None):
            structure["graphs"]=self.graphs
        if (self.group_by!=[] and self.group_by != None):
            structure["group_by"]=self.group_by
        if (self.having!=[] and self.having != None):
            structure["having"]=self.having
        if (self.order_by!=[] and self.order_by != None):
            structure["order_by"]=self.order_by
       
        return structure
            
    def __dict__(self):
        body = { Dialects.CSPARQL: self._to_string_csparql, 
                 Dialects.CQELS: self._to_string_cqels }[self.dialect]().__str__()
        return {"name":self.name, "body": body, "type": self.query_type, "dialect":self.dialect.name,
                "structure":self._structure() }
               
    def __str__(self):
        return self.__dict__().__str__()
        
    def __repr__(self):
        return self.__str__()
    
    def set_experiment(self, e):
        self.experiment = e
    
