import simpy
import random
import networkx as nx
import matplotlib.pyplot as plt
from math import sqrt
from utilities.Node import Node
import sys

#Scenario setup
c = 4
centralNodeScenario = input("Select scenario (input 1 or 2). The first scenario is the bottleneck scenario, the second one is random graph scenario: ")
dynamicFailureStudy = False
if centralNodeScenario != '1' and centralNodeScenario != '2' and centralNodeScenario.lower() != 'one' and centralNodeScenario.lower() != 'two':
	print("Error invalid scenario input")
	sys.exit(1)
if centralNodeScenario == '1' or centralNodeScenario == 'one':
	centralNodeScenario = True
else:
	centralNodeScenario = False
	dynamicFailureStudy = input("Abilitate dynamic failure study? This will make the simulation run up to time 400 and at time 300 50% of the nodes will be randomly removed to study how the protocol responds to such a massive failure. Other parameters will not be calculated since it's a completely different study: the view size is 8 instead of 4 to better tolerate this massive node failure, and only the dynamic self-healing capacity will be measured. Yes or no to continue: ")
	if dynamicFailureStudy.lower() != "yes" and dynamicFailureStudy.lower() != "no" and dynamicFailureStudy.lower() != 'y' and dynamicFailureStudy.lower() != 'n':
		print("Error input")
		sys.exit(1)
	elif dynamicFailureStudy.lower() == "yes" or dynamicFailureStudy.lower() == "y":
		dynamicFailureStudy = True
		c = 8
	else:
		dynamicFailureStudy = False

#Environment setup
env = simpy.Environment()
env.dyn = False
env.communication_channel = simpy.FilterStore(env)
env.lag = 10
env.nodeList = []
env.peerSelectionMode = input("Enter the peer selection mode, choosing between 'random', 'tail' or 'head' (head not advised, results in severe clustering): ")
env.viewSelectionMode = input("Enter the view selection mode, choosing between 'random', 'head' or 'tail' (tail not advised. cannot handle joining nodes well): ")
if (env.peerSelectionMode != "random" and env.peerSelectionMode != "tail" and env.peerSelectionMode != "head") or (env.viewSelectionMode != "random" and env.viewSelectionMode != "head" and env.viewSelectionMode != "tail"):
	print("Error invalid mode was chosen!")
	sys.exit(1)
env.T = 1
env.push = True #we actually never want to disable this since pull-only policy doesn't work 
env.pull = input("Abilitate pushpull? By choosing no there is the possibility of network partition and thus of failure of the simulation. Yes or No to continue: ")
if env.pull.lower() != "yes" and env.pull.lower() != "no" and env.pull.lower() != "y" and env.pull.lower() != "n":
	print("Error input!")
	sys.exit(1)
if env.pull.lower() == "yes" or env.pull.lower() == "y":
	env.pull = True
else:
	env.pull = False


env.plot = input("Abilitate graph plotting? Plotting will start at time 1 of the simulation and update each lag units of time, so this will plot 300/lag images to describe graph evolution. Yes or no to continue: ")

if env.plot.lower() != "yes" and env.plot.lower() != "no" and env.plot.lower() != "y" and env.plot.lower() != "n":
	print("Error input!")
	sys.exit(1)

if env.plot.lower() == "yes" or env.plot.lower() == 'y':
	env.plot = True
	env.lag = input("Enter the desired value for time lag of simulation graph plotting (10, 30 or 100 are advised), the value must be between 1 and 100: ")
	if not env.lag.isdigit():
		print("Error input")
		sys.exit(1)
	else:
		if(env.lag > 100 or env.lag < 1):
			print("Error invalid number")
			sys.exit(1)
		env.lag = int(env.lag)
	
else:
	env.plot = False

#Data structures to collect data from both scenarios 
env.x = 0
env.firstanalysis = True
env.secondanalysis = False
env.deadLinks = []
avg_node_degree = []
max_node_deg = []
min_node_deg = []
avg_shortest_path_length = []
clustering_coefficient = []

#In scenario 2 we also need to keep track of the evolution of 50 nodes during 300 cycles (units of time) and of the mean degree Dk of cycle k over all nodes
deg_evolution = {}

def nodes_generator(env, num_nodes): #for scenario 1
	step = 1
	while True:
		for i in range(1+(env.x*step), (num_nodes+1)+(env.x*step)):
			if i != 1:
				n = Node(env, i, centralNodeScenario)
				env.nodeList.append(n)
		env.x = env.x + 1
		yield env.timeout(1) #One node generated at every time unit
		if env.x == 100:
			break #we don't generate more than 100 nodes
			
def calculate_degree_distribution(graph):
#we calculate max, min and average degree of a node in the graph
#Degree of nodes is important with regards to failure tolerance (dependability) analisys
	min_deg = (0,1000)
	max_deg = (0,0)
	avg_deg = 0
	degrees = []
	#To calulcate degree of a node we both have to look at the node's view and to look at every other node's view to see if there
	for node in graph.nodes:
		deg = graph.degree(node)
		degrees.append((node, deg))
	for tup in degrees:
		if tup[1] < min_deg[1]:
			min_deg = tup
		if tup[1] > max_deg[1]:
			max_deg = tup
		avg_deg = avg_deg + tup[1]
	avg_deg = avg_deg / graph.number_of_nodes()

	#We collect the data to plot
	avg_node_degree.append((avg_deg, env.now))
	max_node_deg.append((min_deg[1], env.now))
	min_node_deg.append((max_deg[1], env.now))
	
def calculate_avg_path_length(graph):
	avg = nx.average_shortest_path_length(graph)
	avg_shortest_path_length.append((avg, env.now))
	
def calculate_clustering_coefficient(graph):
	cc = nx.average_clustering(graph)
	clustering_coefficient.append((cc, env.now))
	
def plot_data(data, name):
	#data is a list of tuples (value, time)
	values, times = zip(*data)
	plt.plot(times, values, marker='o', linestyle='-', color='b')
	plt.title('Time Series Plot')
	plt.xlabel('Time')
	plt.ylabel(name)
	plt.grid(True)
	plt.savefig(name+".png")
	plt.show()
		
				
def show_graph_and_calculate_parameters(env):
	#The graph has a directed edge (u,v) if and only if u has the descriptor of v. However we consider undirected graphs since the passive party will know about the active party when an exchange of information is taking place
	edges = []
	for node in env.nodeList:
		v = node.view
		this_node_id = node.id
		for vertex in v:
			node_id = int(vertex[0][1:])
			edges.append( (this_node_id, node_id) )
	graph = nx.Graph()
	graph.add_edges_from(edges)

	if not nx.is_connected(graph):
		#Some runs in some cases (depends on policy choice) may result in partitions. We analyze only the non partitioned runs.
		print("Graph has been partitioned, simulation will stop. Please restart the simulation.")
		sys.exit(1)
	
	#We calculate the dependability and performance parameters
	calculate_degree_distribution(graph)
	calculate_avg_path_length(graph)
	calculate_clustering_coefficient(graph)
		
	#we draw the plot if the user wants to
	if env.plot:
		print(f"Plotting graph at time {env.now}")
		
		nx.draw(graph, nx.spring_layout(graph), with_labels=True)
		plt.savefig("graph_plot"+str(env.now)+".png")
		plt.show()

def calculate_parameters(env):
	while True:
		if dynamicFailureStudy:
			
			show_graph_and_calculate_parameters(env)
			yield env.timeout(50)
		else:
			if env.firstanalysis:
				env.firstanalysis = False
				env.secondanalysis = True
				yield env.timeout(1)
			elif env.secondanalysis:
				yield env.timeout(env.lag-1)
				env.secondanalysis = False
			else:
				yield env.timeout(env.lag)
			show_graph_and_calculate_parameters(env)
		
		
		
def construct_random_overlay_network(env, centralNodeScenario):

	for i in range(1,101):

		node = Node(env, i, centralNodeScenario)
		env.nodeList.append(node)
		
	for node in env.nodeList:
		num = random.randint(1, node.c)
		while len(node.view) < num:
		
			n = random.choice(env.nodeList)
			if n != node:
				node.view.append([str(n), random.randint(1,100)])
				
	#Insert 50 nodes out of 100 in the dictionary in key/value pairs:ì -->  {n1 : [(value_1, time_1), (value2, time2)...], n2 : ...}
	for i in range(50):
		deg_evolution[str(env.nodeList[i])] = []
		
		
def track_node_degrees(env):
	#we reconstruct the graph and then calculate for each of the 50 nodes the degree at time {env.now}
	#We keep track of the degrees of the nodes and how they change over 300 consecutive cycles
	while True:
		if dynamicFailureStudy and env.now == 300:
			break
		edges = []
		for node in env.nodeList:
			v = node.view
			this_node_id = node.id
			for vertex in v:
				node_id = int(vertex[0][1:])
				edges.append( (this_node_id, node_id) )
		graph = nx.Graph()
		graph.add_edges_from(edges)
		
		for node in deg_evolution:
			node_id = int(node[1:])
			deg = graph.degree[node_id]
			deg_evolution[node].append( (deg, env.now) )
			
		yield env.timeout(1)
			
def calculate_params_scenario_two(deg_evolution):
	#For each node i we calculate di, the mean degree of i over 300 consecutive cycles
	d_list = []
	for node in deg_evolution:
		di = 0
		val_list = deg_evolution[node]
		for tup in val_list:
			di = di + tup[0]
		di = di / 300
		d_list.append( [node, di] )
		
	#We calculate d as the mean of the di s
	d = 0
	for i in d_list:
		d = d + i[1]
	d = d / 50
	
	#We calculate the empirical variance and standard deviation
	var = 0
	for i in d_list:
		var = var + (i[1] - d)**2
	var = var / 49
	
	std_dev = sqrt(var)
	
	print(f"Value of mean degree is: {d}")
	print(f"Value of degree variance is: {var}")
	print(f"Value of degree standard deviation is: {std_dev}")
	
	with open("Statistical values.txt", 'w') as f:
		f.write(f"Node Degree dynamic data over 300cycles\nMean			var			std_dev\n{d}	{var}	{std_dev}")
	
	
	#Autocorrelation calculation: lag k goes from 1 to 150, we choose node n1
	val_list = deg_evolution['n1']
	di = d_list[1][1]
	k_values = []
	for k in range(0, 151):
		dividend = 0
		divisor = 0
		for j in range(300-k):
			dividend = dividend + (val_list[j][0] - di)*(val_list[j + k][0] - di)
		for j in range(300):
			divisor = divisor + (val_list[j][0] - di)**2
		rk = dividend / divisor
		k_values.append( (rk, k) )
		
	plot_data(k_values, "Autocorrelation with respect to lag value k")
	
def static_failure_study(env):
	#In this study we take the graph at cycle 300 and start removing nodes one at a time. We are interested in seeing how many nodes we remove until a partition happens
	#The nodes are chosen randomly and the experiment is run 100 times to get an average. The paper did 800 experiments so we will too.
	
	#Build graph in cycle 300
	edges = []
	for node in env.nodeList:
		v = node.view
		this_node_id = node.id
		for vertex in v:
			node_id = int(vertex[0][1:])
			edges.append( (this_node_id, node_id) )
	#graph = nx.Graph()
	#graph.add_edges_from(edges)
	
	#Initialize list
	avg_percentage_values = []
	for i in range(1,97):
		avg_percentage_values.append( [0, i] ) # we have (value between 0 and 1 percentage of partitions happened, percentage points of nodes removed from the total)

	#Calculate values
	for j in range(800):
		G = nx.Graph() #copy of the graph
		G.add_edges_from(edges)
		percentage_values = []
	
		for i in range(1,97):
			random_node = random.choice(list(G.nodes()))
			G.remove_node(random_node)
			if nx.is_connected(G):
				percentage_values.append( (0, i) )
			else:
				percentage_values.append( (1, i) )

		for p in range(96):
			avg_percentage_values[p][0] = avg_percentage_values[p][0] + percentage_values[p][0]
		
	#Calculate averages
	for i in avg_percentage_values:
		i[0] = i[0] / 800	
	
	percentage, values = zip(*avg_percentage_values)
	plt.plot(values, percentage, marker='o', linestyle='-', color='b')
	plt.title('Tolerance to node failure')
	plt.xlabel('Percentage unit')
	plt.ylabel("Average number of partitions per percentage unit")
	plt.grid(True)
	plt.savefig("StaticFailureToleranceStudy.png")
	plt.show()		
		
def is_overlay_connected(env):
	edges = []
	for node in env.nodeList:
		v = node.view
		this_node_id = node.id
		for vertex in v:
			node_id = int(vertex[0][1:])
			edges.append( (this_node_id, node_id) )
	graph = nx.Graph()
	for node in env.nodeList:
		graph.add_node(node.id)
	
	graph.add_edges_from(edges)
	
	
	if nx.is_connected(graph):
		return True
	else:
		return False	
		
def selfHeal(env):
	yield env.timeout(300)
	print("Starting dynamic failure study: 50% of nodes will be eliminated to study the self-healing capacity")
	#We repeat the elimination of 50% of the nodes until we find the first connected graph to study
	num_eliminated = 0
	while(num_eliminated < len(env.nodeList) // 2):
		to_delete = random.choice(env.nodeList)
		deleted_from_list = []
		for node in env.nodeList:
			retry = False
			for view_elem in node.view:
				if view_elem[0] == str(to_delete):
					node.view.remove(view_elem)
					if is_overlay_connected(env):
						deleted_from_list.append([view_elem, node])
					else:
						#if the node deletion causes a partition we rollback the entire operation
						node.view.append(view_elem)
						node.quickSortView(node.view)
						for del_elem in deleted_from_list:
							del_elem[1].view.append(del_elem[0])
							del_elem[1].quickSortView(del_elem[1].view)
						
						retry = True
			if retry:
				break
		if not retry:
			#We successfully removed the node from the graph without causing partitions
			env.nodeList.remove(to_delete)
			to_delete.activeThread.stop()
			to_delete.passiveThread.stop()
			num_eliminated = num_eliminated + 1
	
	#We start counting number of overall dead links per time unit to assess self-healing capacity of the network
	while True:
		num_dl = 0
		
		for node in env.nodeList:
			num_dl = num_dl + node.c - len(node.view) #update number of dead links
			
			
		#Store number of dead links for current cycle
		env.deadLinks.append( (num_dl, env.now) )
		yield env.timeout(1)				
		
		
env.c = c			
env.selfHealStudy = dynamicFailureStudy
if centralNodeScenario:
	#In the first scenario at time 1 we have only the first node (central), at time two we have 2 nodes, at time 3 3, and so on until time 100 (we should have 100 nodes by time 100 and stop adding more nodes and see how does the network converge). Each node boots up with the descriptor of the central node (the first one) so that at the start it can only exchange information with the central node. Many of these nodes will converge to a topology in which each node knows about 3 or 4 other nodes in the overlay and not necessarily about the first node. Any optimizations are not allowed in order to better focus on the core protocols. Partitions are possible but are not considered for obvious reasons.
	node_1 = Node(env, 1, centralNodeScenario)
	env.centralNode = node_1
	env.nodeList.append(node_1)
	env.process(nodes_generator(env, 1))
	env.process(calculate_parameters(env))
	env.run(until=301)
	#Plot Degree distribution data, average path data, and clustering coefficient data at cycle 300
	plot_data(avg_node_degree, "Average node degree")
	plot_data(max_node_deg, "Max node degree")
	plot_data(min_node_deg, "Min node degree")
	plot_data(avg_shortest_path_length, "Average shortest path length")
	plot_data(clustering_coefficient, "Clustering coefficient")
	
else:
	
#In the second scenario we start with a random graph of 100 nodes and see its evolution. The views of the nodes are initialized with c random descriptors. We do not have the "bottlneck" problem of the first scenario anymore, we run for 300 cycles (units of time) the random graph and see its evolution.
	
	construct_random_overlay_network(env, centralNodeScenario)
	if dynamicFailureStudy:
		#At time 300 we eliminate 50% of the nodes and (with a connected graph) study how the protocol behaves
		#The view size will be increased from 4 to 30. The reason for this increase is that a view of 4 is small and view size influences directly node removal tolerance, so the least tolerant protocols like (random, head, pushpull) are going to be able to lose 50% of the nodes without suffering a partition. In fact data shows that if we run the simulation with a view of 4 we practically always get a partition for certain protocols, hence the simulation will run for an infinite amount of time.
		#The number of dead links will be counted
		env.process(selfHeal(env))
		env.dyn = True
		if env.plot:
			env.process(calculate_parameters(env))
		env.run(until=351)
		plot_data(env.deadLinks, "Number of dead links")
	else:
		env.process(calculate_parameters(env))
		env.process(track_node_degrees(env))
		env.run(until=301)
		#Plot Degree distribution data, average path data, and clustering coefficient data at cycle 300
		plot_data(avg_node_degree, "Average node degree")
		plot_data(max_node_deg, "Max node degree")
		plot_data(min_node_deg, "Min node degree")
		plot_data(avg_shortest_path_length, "Average shortest path length")
		plot_data(clustering_coefficient, "Clustering coefficient")
		calculate_params_scenario_two(deg_evolution)
		static_failure_study(env)

