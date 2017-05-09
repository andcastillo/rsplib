from report import Report
from rdflib import Graph, plugin 
from rdflib.serializer import Serializer


report = Report("exp1","experiment1", "An experiment", "n3")

report.add_experiment("experiment1_jsonld", "Experiment1 DOE", "http://example.org/exp1.jsonld")

report.add_cpu("experiment1_cpu", "Experiment1 CPU", "15 minutes", "http://example.org/exp1-cpu.csv")
report.add_memory("experiment1_memory", "Experiment1 CPU", "15 minutes", "http://example.org/exp1-cpu.csv")
report.add_results("experiment1_query_results", "Experiment1 Results", 
		"CSPARQL", "Q1, Q2")

report.add_result("experiment1_Q1_results","experiment1 Q1 results","Q1",  "SELECT * WHERE {?s ?p ?o}", "http://example.org/Q1.ttl")
report.add_result("experiment1_Q2_results","experiment1 Q2 results","Q2",  "SELECT * WHERE {?s2 ?p2 ?o2}", "http://example.org/Q2.ttl")

report.add_default_licence()
report.serialize("exp1", "n3")
report.serialize("exp1", "json-ld")
report.serialize("exp1", "nt")
report.serialize("exp1", "trig")
report.serialize("exp1", "rdf")

