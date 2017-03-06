from RSPClient import RSPClient
import websocket
import thread
import time

def on_message(ws, message):
    print message

def on_error(ws, error):
    print error

def on_close(ws):
    res = rsp.unregister_observer('query1', 'observer1');
    print "### closed ###"

if __name__ == "__main__":
    rsp = RSPClient("http://localhost", 8181);

    res = rsp.register_stream('str1', 'http://192.168.99.100:4000/sgraph');
    print res
    res = rsp.register_query('query1', 'REGISTER STREAM query1 AS CONSTRUCT {?s ?p ?o} FROM STREAM <str1> [RANGE 1m STEP 1m] WHERE {?s ?p ?o}');
    print res
    res = rsp.new_observer('query1', 'observer1', {'type':'ws', 'host':'localhost', 'port': 8282});

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(res['observer']['dataPath'],
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.run_forever()