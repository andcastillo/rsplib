import time
from sys import argv
from rsplib.processing.sink import BaseSink

web_socket=argv[1] # ro['observer']['dataPath'], 
query=argv[2] #q['name'], 
file_path=argv[3] #root+"/"+q["result_path"]+ro['id']+"/"
duration = argv[4]
unit = argv[5]
report_string = argv[6]

print("Building RSP Collector")

intervals = [
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
        ]

for i in intervals:
    if (unit == i[0]):
         duration = duration * i[1]

timeout = time.time() +  duration)  # 5 minutes from now

r = RSPCollector(web_socket, query, file_path, report_string)

try:
    while True:
        time.sleep(10)
        if time.time() > timeout:
            break
except KeyboardInterrupt:
    print('interrupted!')
