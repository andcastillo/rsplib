from websocket import WebSocketApp
import threading, os

class RSPCollector(WebSocketApp):

    result_file = None
    def on_message(self, obj, message, *args):
        self.result_file.write(message)
        self.result_file.write('\n')

    def on_error(self, obj, error, *args):
        self.result_file.write(error)
        self.result_file.write('\n')
        self.result_file.close()

    def on_close(self, *args):
        print "### closed ###"
        self.result_file.close()

    def __init__(self, url, query, observer, result_path):
        super(RSPCollector, self).__init__(
            url=url,
            on_message = self.on_message    ,
            on_error = self.on_error,
            on_close = self.on_close)
        self.query = query;
        self.observer = observer;
        self.result_path = result_path; 

        self.result_path = result_path
        if not os.path.exists(self.result_path):
            os.makedirs(self.result_path)
        
        self.result_file = open(self.result_path+query+".res", "w+")

        t=threading.Thread(target=self.run_forever)
        t.setDaemon(True)
        t.start()