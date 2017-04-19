
class Query:
    def set_select_clause(self,select):
        self.select_clause = select
    
    def set_where_clause(self,where):
        self.where_clause = where
    
    def add_windowed_stream(self,stream,range,step):
        self.streams.append({"name":stream,"range":range,"step":step})
    
    def add_dataset(self,dataset):
        self.datasets.append(dataset)
    
    def to_string_csparql(self):
        query = ""
        if(self.query_type=="query"):
            query += "SELECT "
        else:
            query += "CONSTRUCT "
        
        query+=self.select_clause+" "        
        for s in self.streams:
            streamQuery = "FROM STREAM <"+s["name"]+"> [RANGE "+s["range"]+" STEP "+ s["step"] +"] \n"
            query+=streamQuery
        
        for d in self.datasets:
            datasetQuery = "FROM <"+d+">\n"
            query+=datasetQuery
            
        query+="WHERE "
        query+=self.where_clause
        return query
    
    def to_string_cqels(self):
        query=""
        return query
    
    def __init__(self,name,query_type):
        self.select_clause= ""
        self.where_clause= ""
        self.query_type = query_type
        self.name= name
        self.streams = []
        self.datasets = [] 