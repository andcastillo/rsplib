import rsp, json

e = rsp.Experiment()

d = rsp.Dialects.CSPARQL

e.add_engine('http://csparql.westeurope.cloudapp.azure.com', 8182, d)

s = e.add_query("Q1", "query", d).add_stream("str1", "http://str1.com").add_window(10, 5)

q = e.get_query("Q1").add_windowed_stream("str2", "http://str2.com", 15,15)

q = q.add_windowed_stream("str3", "http://str3.com", 20,20)


d = e.get_query("Q1").add_dataset("name", "http://dataset.rdf", serialization="RDF/XML", default=True)

q.set_select_clause("?obId1 ?obId2 ?v1 ?v2 ")
q.set_where_clause("{?p1   a <http://www.insight-centre.org/citytraffic#ParkingVacancy>. ?p2   a <http://www.insight-centre.org/citytraffic#CongestionLevel>. {?obId1 a ?ob. ?obId1 <http://purl.oclc.org/NET/ssnx/ssn#observedProperty> ?p1. ?obId1 <http://purl.oclc.org/NET/sao/hasValue> ?v1.?obId1 <http://purl.oclc.org/NET/ssnx/ssn#observedBy> <http://www.insight-centre.org/dataset/SampleEventService#AarhusParkingDataKALKVAERKSVEJ>. }{?obId2 a ?ob.?obId2 <http://purl.oclc.org/NET/ssnx/ssn#observedProperty> ?p2.?obId2 <http://purl.oclc.org/NET/sao/hasValue> ?v2.?obId2 <http://purl.oclc.org/NET/ssnx/ssn#observedBy> <http://www.insight-centre.org/dataset/SampleEventService#AarhusTrafficData158505>.}}")



e1 = rsp.open_remote('https://rsplab.blob.core.windows.net/experiments/experiment.json')


print e

print "---"
print e1