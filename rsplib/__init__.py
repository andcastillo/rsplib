from IPython.display import FileLinks
from influxdb import DataFrameClient
from pandas import DataFrame

#def report_publish(exec):
#	client = DataFrameClient('influxsrv', 8086, 'root', 'root', 'rspengines')
#	where = "WHERE time > " + str(exec.experiment_execution['start_time']) + " and time < "+str(exec.experiment_execution['start_time']) + " and run.engine="+str(exec.experiment_execution['E'].lowers()=+ " and run.uuid="+str(exec.experiment_execution['engine_uuid'])+";"
#	
#	cpu_steady = client.query("SELECT value, time FROM cpu_usage_total "+ where, database='rspengines')
#	
#	cpu_steady['cpu_usage_total'].to_csv('./data/cpu_usage_total.csv',columns = ["", "value"], sep=",")
#	memory_steady = client.query("SELECT value, time FROM memory_usage "+ where, database='rspengines')
#	memory_steady['memory_usage'].to_csv('./data/cpu_usage_total.csv',columns = ["", "value"], sep=",")
#
#	FileLinks('./data')