import json, os
import requests
from enum import Enum
import datetime, time

from rsplib.processing.consumer import RSPEngine
from rsplib.experiments import Experiment, ExperimentExecution

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
    engine = RSPEngine(experiment.engine()['host'], experiment.engine()['port']);
    
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
            ro = engine.new_observer(q.name, "default", {"host":experiment.engine()['host'],"type":"ws","port":9101,"name":"default"}); 
            execution.add_observer({q.name:ro})
            execution.add_queries(engine.queries());
    
    return execution

def now():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

def execute(execution, stream_running=True, collect=False):
    
    engine = RSPEngine(execution.experiment.engine()['host'], execution.experiment.engine()['port']);
        
    execution.set_start(now())
    
    #print(experiment_execution)
    #report=json.dumps(experiment_execution, indent=4, sort_keys=True)
    
    root = execution.experiment_execution['E']['runUUID']
    
    if not os.path.exists(root):
        os.makedirs(root)

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

    time.sleep(amount)
    
    execution.set_end(now())

    #print("Terminating at "+ str(datetime.datetime.fromtimestamp(now()).strftime('%Y-%m-%d %H:%M:%S')))
    print("Terminating the experiment")               
    for q in engine.queries():
        for o in engine.observers(q["id"]):
            engine.unregister_observer(q["id"], o["id"])
        engine.unregister_query(q["id"])
    for s in engine.streams():
        engine.unregister_stream(s["streamURL"])
    
#end
