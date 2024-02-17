import simpy
import copy
class ActiveThread:
	def __init__(self, env, node_id, node):
		self.env = env
		self.node_id = node_id
		self.node = node
		self.communication_channel = env.communication_channel
		self.process = env.process(self.run())
	
	def stop(self):
		self.process.interrupt("Stop Thread")	
		
	#We mimick the skeleton protocol for the active thread
	def run(self):
		try:
			while(True):
				#Wait T time units
				yield self.env.timeout(self.env.T)
				
				p = self.node.selectPeer(self.env.peerSelectionMode)
				if p == None:
					continue
				pid = int(p[1:])
	
				#if push block
				if self.env.push:
					myDescriptor = [str(self.node), 0]
					#Buffer = merge(myView, {myDescriptor})
					buf = self.node.mergeViews([myDescriptor])
					buff = copy.deepcopy(buf) #avoid the receiver doing side effect on the sender's data structure 
					#Send buffer to p
					yield self.communication_channel.put({'data': buff, 'receiver': pid, 'sender': self.node_id})

				else:
					#Send {} to p
					yield self.communication_channel.put({'data': [],'receiver': pid, 'sender': self.node_id})
					
				if self.env.pull:
					#receive view from p
					message = yield self.communication_channel.get(lambda item: item['receiver'] == self.node_id and item['sender'] == pid)
					if message != None:
					
						view2 = message['data']
						self.node.increaseHopCount(view2)
						
						buff = self.node.mergeViews(view2)
						self.node.cleanView(buff)
						self.node.view = self.node.selectView(self.env.viewSelectionMode,buff)
					else:
						pass
				
		except simpy.Interrupt as interrupt:
			if interrupt.cause == "Stop Thread":
				pass
			else:
				print("Unknown error, stopping thread")
				pass
					
