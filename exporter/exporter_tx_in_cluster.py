#!/usr/bin/env python3
import networkx as nx
import pickle

from sys import argv

try:
	f = argv[1]
except:
	f = '../grapher/tx_graph.dat'

# Config
# Cluster number
cluster_n = 11259

with open(f, "rb") as infile:
	G = pickle.load(infile)

print("Graph loaded.")

with open("../clusterizer/clusters.dat", "rb") as cf:
	users = pickle.load(cf)

print("Clusters loaded.")

addresses = set()
for address, cluster in users.items():
	if cluster == cluster_n:
		addresses.add(address)
print("%d addresses loaded." % len(addresses))

nodes, edges = set(), []

with open(str(cluster_n) + ".dot", 'w') as f:
	f.write('digraph G {\n');

	for u, v, d in G.edges_iter(data=True):
		#if (u not in addresses or v not in addresses):
		if (u not in addresses and v not in addresses):
			continue

		n_of_tx = d['number_of_transactions']

		nodes.add(u)
		nodes.add(v)
		edges.append((u, v, n_of_tx))

	print("Filtering results: %d nodes and %d edges." % (len(nodes), len(edges)))
	print("Generating a DOT file...")

	nodes = sorted(list(nodes))

	for n in nodes:
		recv = str(int(G.node[n].get('amount_received', 0)))
		f.write('"%s" [recv=%s];\n' % (n, recv))

	del G
	f.write('\n')

	for edge in edges:
		(u, v, n_of_tx) = edge
		f.write('"%s" -> "%s" [weight=%s];\n' % (u, v, str(n_of_tx)))

	f.write('};\n')
