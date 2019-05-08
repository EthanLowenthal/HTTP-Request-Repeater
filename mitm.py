import asyncio
import sys

class Addon:
	def __init__(self, queue, lock):
		self.queue = queue
		self.lock = lock
		self.intercept = False
		self.intercepted_flows = []
		self.repeating = None

	def request(self, flow):
		flow.dropped = False

		if flow.request.host_header + flow.request.path == self.repeating:
			return

		if self.intercept:
			if not ('test' in sys.argv and flow.request.host_header == '127.0.0.1:5000'):
				flow.intercept()
				self.intercepted_flows.append(flow)

		else:
			self.queue.put(flow)

	def response(self, flow):
		if flow.dropped:
			flow.response.content = b""

def start_mitm(master):
	asyncio.set_event_loop(master.channel.loop)
	master.run()