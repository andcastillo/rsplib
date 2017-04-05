from sys import argv
from RSPCollector import RSPCollector

url=argv[1] # ro['observer']['dataPath'], 
query=argv[2] #q['name'], 
file_path=argv[3] #root+"/"+q["result_path"]+ro['id']+"/"

r = RSPCollector(url, query, file_path)
