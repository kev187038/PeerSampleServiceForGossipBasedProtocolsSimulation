import simpy
import random
import sys
from utilities.ActiveThread import ActiveThread
from utilities.PassiveThread import PassiveThread
class Node:
	def __init__(self, env, node_id, centralNodeScenario):
		self.env = env
		#Address of the node
		self.id = node_id 
		#We set view list and max number c 
		self.view = []
		self.c = env.c
		
		self.process = env.process(self.run())
		
		#Declare both active and passive threads
		self.activeThread = ActiveThread(self.env, self.id, self)
		self.passiveThread = PassiveThread(self.env, self.id, self)
		
		#In the first scenario the central node is the first node that boots up and knows about all the nodes
		if centralNodeScenario and node_id != 1:
			self.view.append(['n1', 1])
		
		
	def __repr__(self):
	
		return "n" + str(self.id) #useful to print list of nodes
		
	def __str__(self):
		
		return "n" + str(self.id)
		
	def __eq__(self, other):
		if isinstance(other, Node):
			return self.id == other.id
		else:
			return False
		
	
	#selectPeer selects at random, tail, or head depending on the mode, and it returns 1 node.
	def selectPeer(self, mode):
	
		if mode == "random":
			if(len(self.view) > 0):
				return random.choice(self.view)[0]
			else:
				return None
			
		elif mode == "tail":
			if(len(self.view) > 0):
				return self.view[-1][0]
			else:
				return None
			
		elif mode == "head":
			if(len(self.view) > 0):
				return self.view[0][0]
			else:
				return None
		else:
			print(f"Error in specified mode {mode}")
			sys.exit(1)
			
	#Each descriptor is represented by a tuple [<n+id>, hop_count]	
	def isPresent(self, v, node):
	
		for i in v:
		
			if i[0] == node:
			
				return True
				
		return False
		
	def quickSortView(self, view):
		if len(view) <= 1:
			return view
		
		pivot = view[len(view) // 2][1]
		left = [x for x in view if x[1] < pivot]
		middle = [x for x in view if x[1] == pivot]
		right = [x for x in view if x[1] > pivot]
		return self.quickSortView(left) + middle + self.quickSortView(right)
		
		
    		
	#Select view selects c elements from a view in the specified mode
	def selectView(self, mode, view):
		selection = []
		#if the view has less than c elements we will choose all elements anyway
		if(self.c >= len(view)):
				selection = view
		elif mode == "random":
			while len(selection) < self.c:
				elem = random.choice(view)
				if not self.isPresent(selection, elem[0]):
					selection.append(elem)
			selection = self.quickSortView(selection)
				
		elif mode == "head":
		
			selection = view[:self.c]
			
		elif mode == "tail":
		
			selection = view[-self.c:]
			
		return selection
				
			
	def getNodeView(self):
	
		return self.view
		
	def getNodeId(self):
	
		return self.id
	
	#increaseHopCount increases hopcount of every descriptor
	def increaseHopCount(self, v):
		
		for i in v:
		
			i[1] = i[1] + 1
						
	#This function merges the view of the node with the provided view in increasing order of hops and, as said in the paper, if two nodes are present in the views, we choose the node with the lower hop count

	def mergeViews(self, view2):
		view1 = self.view
		merge = []
		i = 0
		j = 0
		
		while i < len(view1) and j < len(view2):

			desc1 = view1[i]
			
			desc2 = view2[j]
			
			if desc1[1] < desc2[1]:
			
				if not self.isPresent(merge, desc1[0]):
					merge.append(desc1)
				
				i = i + 1
				
			else:

				if not self.isPresent(merge, desc2[0]):
					merge.append(desc2)
				
				j = j + 1
		
		while i < len(view1):
			if not self.isPresent(merge, view1[i][0]):
				merge.append(view1[i])
			i = i + 1
				
		while j < len(view2):
			if not self.isPresent(merge, view2[j][0]):
				merge.append(view2[j])
			j = j + 1
		
		return merge
	
	#The node's view does not contain the node itself
	def cleanView(self, view):
		for i in view:
			if i[0] == str(self):
				view.remove(i)
			
	def run(self):

		print(f"Node {self.id} starts up at time {self.env.now}")
			
		yield self.env.timeout(simpy.core.Infinity)
