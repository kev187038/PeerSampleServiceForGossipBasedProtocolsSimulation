import simpy
import copy
class PassiveThread:
	def __init__(self, env, node_id, node):
		self.env = env
		self.node_id = node_id
		self.node = node
		self.communication_channel = env.communication_channel
		self.process = env.process(self.run())

		
	def stop(self):
		self.process.interrupt("Stop Thread")	
		
	#We mimick the skeleton protocol for the passive thread
	def run(self):
		try:
			while(True):
				if self.env.dyn: #in the dynamic study we don't want pushpull protocols to have unfair advantages on a small sample
					yield self.env.timeout(1)
				
				message = yield self.communication_channel.get(lambda item: item['receiver'] == self.node_id)
				viewp = message['data']
				p = message['sender']
				self.node.increaseHopCount(viewp)

				#if pull is enabled we send back our descriptors
				if self.env.pull:
					#0 initial hop count
					myDescriptor = [str(self.node), 0]
					buf = self.node.mergeViews([myDescriptor])
					buff = copy.deepcopy(buf)
					yield self.communication_channel.put({'data': buff, 'receiver': p, 'sender': self.node_id})
				
				buff = self.node.mergeViews(viewp)
				self.node.cleanView(buff)
				self.node.view = self.node.selectView(self.env.viewSelectionMode, buff)
		
		except simpy.Interrupt as interrupt:
			if interrupt.cause == "Stop Thread":
				pass
			else:
				print("Unknown error, stopping thread")
				pass
				
