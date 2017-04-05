import time, json, time, os
from RSPClient import RSPClient
from RSPCollector import RSPCollector
from sys import argv

tobserve = []
rsp = None
experiment_execution={}

def w(p, i):
    experiment_execution[p] = i
    
with open(argv[1]) as input_file:    
    experiment = json.load(input_file)

rsp = RSPClient(experiment['engine']['host'], experiment['engine']['port']);

experiment_execution['!Experiment'] = experiment
experiment_execution['E'] = rsp.engine()
experiment_execution['D'] = experiment['static']
experiment_execution['S'] = None
experiment_execution['Q'] = []
experiment_execution['K'] = None # save the KPIs
experiment_execution['R'] = None # save the result location

root = experiment_execution['E']['runUUID']

if not os.path.exists(root):
            os.makedirs(root)

streams=[]
for s in experiment['streams']:
    	print "Registering stream: " + str(s['name'])
    	streams.append(rsp.register_stream( s['name'], s['location'] ))

w('S',streams)

for q in experiment['queries']:
    print "Registering query " + q['name'] +" "+ str(q['repeat']) + " times."
    for i in range(0,q['repeat']):
        rsp.register_query(q['name'], q['body'])
        for o in  q['observers']:
            print "Registering observers for "+q['name']+ " : " + o['name']
            ro = rsp.new_observer(q['name'], o['name'], o);
            if o['persist']:
                tobserve.append((q,ro));
        w('Q', rsp.queries());

for (q,ro) in tobserve:
    print ro
    r = RSPCollector(ro['observer']['dataPath'], q['name'], ro, root+"/"+q["result_path"]+ro['id']+"/")
    
print experiment_execution

with open(root+"/"+'report.json', 'w') as outfile:
    pretty=json.dumps(experiment_execution, indent=4, sort_keys=True)
    outfile.write(pretty)
outfile.close()

timeout = time.time() +  1000*60*int(experiment['metadata']['duration'])  # 5 minutes from now

try:
    while True:
        time.sleep(10)
        if time.time() > timeout:
            break
except KeyboardInterrupt:
    print 'interrupted!'


