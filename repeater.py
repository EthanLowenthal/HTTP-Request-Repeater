import tkinter as tk
import requests
from tkinter import ttk
from mitmproxy.net.http.headers import Headers
from random_vals import RandomFromListValue, RandomRangeValue, StaticValue, RandomRegexValue
import time
from threading import Thread

class Sender:
	def __init__(self, repeater, times, delay):
		self.repeater = repeater

		self.times = times
		self.delay = delay

		if self.times == "": self.times = 1
		if self.delay == "": self.delay = 0
		self.delay = float(self.delay)

		self.pause = False
		self.stop = False


	def run(self):
		headers = self.repeater.compile_headers()
		f = getattr(requests, self.repeater.request.method.lower())

		if self.times is not None:
			self.times = int(self.times)

			for i in range(self.times):
				while self.pause:
					time.sleep(1)

				if self.stop:
					return

				time.sleep(self.delay)

				f(self.repeater.request.url, headers=headers, data=self.repeater.compile_body(),
						 hooks={'response': self.repeater.on_response})

		else:
			while True:
				while self.pause:
					time.sleep(1)

				if self.stop:
					return

				time.sleep(self.delay)

				f(self.repeater.request.url, headers=headers, data=self.repeater.compile_body(),
				  hooks={'response': self.repeater.on_response})

class Repeater:
	def __init__(self, window, request):
		self.window = tk.Toplevel(window)
		self.request = request

		repeater_notebook = ttk.Notebook(self.window)
		repeater_notebook.pack(fill=tk.BOTH, expand=1)
		self.headers_frame = tk.Frame(repeater_notebook)
		body_frame = tk.Frame(repeater_notebook)
		settings_frame = tk.Frame(repeater_notebook)
		repeater_notebook.add(self.headers_frame, text='Headers')
		repeater_notebook.add(body_frame, text='Body')
		repeater_notebook.add(settings_frame, text='Settings')

#        ------------------------------ SEND CONTROLS ------------------------------

		send_controls_label_frame = ttk.Labelframe(settings_frame, text='Controls')
		send_controls_label_frame.pack(fill=tk.BOTH, side=tk.TOP, expand=1)

		send_controls_frame = tk.Frame(send_controls_label_frame)
		send_controls_frame.pack(fill=tk.BOTH, expand=1)

		vcmd = (self.window.register(self.validate), '%P')
		temp = tk.Frame(send_controls_frame)
		temp.pack(anchor=tk.W)
		tk.Label(temp, text='times:').pack(side=tk.LEFT)
		self.n_times = tk.Entry(temp, width=4)
		self.n_times.pack(side=tk.LEFT)
		self.n_times.insert(tk.END, '1')
		self.n_times.configure(validate="key", validatecommand=vcmd)

		temp = tk.Frame(send_controls_frame)
		temp.pack(anchor=tk.W)
		tk.Label(temp, text='delay:').pack(side=tk.LEFT)
		self.delay = tk.Entry(temp, width=4)
		self.delay.pack(side=tk.LEFT)
		self.delay.insert(tk.END, '0')
		self.delay.configure(validate="key", validatecommand=vcmd)


		temp = tk.Frame(send_controls_frame, pady=2)
		temp.pack(anchor=tk.W)
		self.send_infinite = tk.Button(temp, text='send infinite',
				  command=lambda :self.send(delay=self.delay.get())
				  )
		self.send_finite = tk.Button(temp, text='send finite',
				  command=lambda :self.send(times=self.n_times.get(), delay=self.delay.get())
				  )
		self.send_one = tk.Button(temp, text='send one', command=lambda: self.send(times=1))

		self.send_infinite.pack(side=tk.LEFT)
		self.send_finite.pack(side=tk.LEFT)
		self.send_one.pack(side=tk.LEFT)

		temp = tk.Frame(send_controls_frame, pady=2)
		temp.pack(anchor=tk.W)
		tk.Button(temp, text='sample request',command=self.compile_request).pack(side=tk.LEFT)
		tk.Button(temp, text='clear responses', command=self.clear_responses).pack(side=tk.LEFT)

		temp = tk.Frame(send_controls_frame, pady=2)
		temp.pack(anchor=tk.W)

		self.pause_button_text = tk.Variable()
		self.pause_button_text.set('pause')
		self.pause_button = tk.Button(temp, textvariable=self.pause_button_text, command=self.toggle_pause, state=tk.DISABLED)
		self.stop_button = tk.Button(temp, text='stop', command=self.stop, state=tk.DISABLED)
		self.pause_button.pack(side=tk.LEFT)
		self.stop_button.pack(side=tk.LEFT)

		self.pause_label = tk.Label(send_controls_frame, text='PAUSED')

		compiled_request_frame = ttk.Labelframe(settings_frame, text='Compiled Request')
		compiled_request_frame.pack(fill=tk.BOTH, side=tk.TOP, expand=1)

#        ------------------------------ RESPONSES ------------------------------

		self.responses_variable = tk.Variable()
		self.responses_variable.set(['Nothing Sent'])
		responses_list = tk.Listbox(settings_frame, listvariable=self.responses_variable)
		responses_list.pack(fill=tk.X, side=tk.TOP, expand=1)

		self.responses = {}

#        ------------------------------ COMPILED REQUEST ------------------------------

		self.compiled_request_veiwer_text = tk.Variable()
		compiled_request_veiwer = tk.Label(compiled_request_frame, textvariable=self.compiled_request_veiwer_text,
										   justify=tk.LEFT)
		compiled_request_veiwer.pack(fill=tk.X, expand=1)
		self.compiled_request_veiwer_text.set('No Reqest Yet')

#        ------------------------------ HEADERS ------------------------------

		self.headers_temp_frame = tk.Frame(self.headers_frame)
		self.headers_temp_frame.pack()

#        ------------------------------ BODY CONTROLS ------------------------------

		controls_frame = ttk.Labelframe(body_frame, text='controls')
		controls_frame.pack(side=tk.BOTTOM, fill=tk.X)
		temp_frame = tk.Frame(controls_frame)
		temp_frame.pack()

		tk.Button(temp_frame, text='static value',
				command=lambda v='static': self.add_custom_value_to_body(v)
				).pack(side=tk.LEFT)

		tk.Button(temp_frame, text='random integer',
				command=lambda v='int': self.add_custom_value_to_body(v)
				).pack(side=tk.LEFT)

		tk.Button(temp_frame, text='random value from list',
				command=lambda v='list': self.add_custom_value_to_body(v)
				).pack(side=tk.LEFT)

		tk.Button(temp_frame, text='random regex',
				command=lambda v='regex': self.add_custom_value_to_body(v)
				).pack(side=tk.LEFT)

#        ------------------------------ BODY TEXT ------------------------------

		self.body_text = tk.Text(body_frame)
		self.body_text.pack(fill=tk.BOTH, expand=1, side=tk.LEFT)

		val_temp_frame = tk.Frame(body_frame)
		val_temp_frame.pack(side=tk.RIGHT, expand=1, fill=tk.Y)

		self.custom_vals = []
		self.custom_vals_variable = tk.Variable(value=self.custom_vals)
		self.custom_vals_variable.set(self.custom_vals)

		self.body_text.bind('<KeyRelease-BackSpace>', lambda e: self.reload_custom_vals())

		self.custom_vals_list = tk.Listbox(val_temp_frame, listvariable=self.custom_vals_variable)
		self.custom_vals_list.pack(fill=tk.BOTH, expand=1, side=tk.TOP)
		self.custom_vals_list.bind("<Double-Button-1>", self.veiw_custom_val)

		self.custom_val_veiwer = tk.Frame(val_temp_frame)
		self.custom_val_veiwer.pack(side=tk.BOTTOM)

		self.body_text.delete('1.0', tk.END)

#        ------------------------------ OTHER STUFF ------------------------------

		self.make_headers_table(request)
		self.body_text.insert(tk.END, request.text)

		self.custom_headers = []

		self.thread = None

	def validate(self, new):
		if new == "":
			return True
		try:
			float(new)
			return True
		except ValueError:
			return False

	def clear_responses(self):
		self.responses = {}
		self.responses_variable.set(['No Request Yet'])

	def on_response(self, response, *args, **kwargs):
		if response.status_code in self.responses.keys():
			self.responses[response.status_code] += 1

		else:
			self.responses[response.status_code] = 1

		list = ["Status: Count"]
		for (k, v) in self.responses.items():
			list.append("{}: {}".format(k, v))

		self.responses_variable.set(list)

	def send(self, times=None, delay=0.0):
		self.pause_button.configure(state=tk.NORMAL)
		self.stop_button.configure(state=tk.NORMAL)

		self.send_infinite.configure(state=tk.DISABLED)
		self.send_finite.configure(state=tk.DISABLED)
		self.send_one.configure(state=tk.DISABLED)

		self.thread = Sender(self, times, delay)
		Thread(target=self.thread.run).start()

	def stop(self):
		if self.thread is not None:
			self.thread.stop = True
		self.thread = None

		self.pause_button.configure(state=tk.DISABLED)
		self.stop_button.configure(state=tk.DISABLED)

		self.send_infinite.configure(state=tk.NORMAL)
		self.send_finite.configure(state=tk.NORMAL)
		self.send_one.configure(state=tk.NORMAL)

	def toggle_pause(self):
		if self.thread is not None:
			self.thread.pause = not self.thread.pause

		if self.thread.pause:
			self.pause_label.pack()
			self.pause_button_text.set('resume')

		else:
			self.pause_label.pack_forget()
			self.pause_button_text.set('pause')

	def veiw_custom_val(self, evt, val=None):
		for slave in self.custom_val_veiwer.pack_slaves():
			slave.pack_forget()

		if val is None:
			custom_val = self.custom_vals[self.custom_vals_list.curselection()[0]]

		else:
			custom_val = val
		custom_val.display()

	def add_custom_value_to_body(self, val):
		if val == 'static':
			btn_text = tk.StringVar()
			button = tk.Button(self.body_text, textvariable=btn_text)
			value = StaticValue('static', button, btn_text, self.custom_val_veiwer)
			button.configure(command=lambda v=value: self.veiw_custom_val(None, val=v))
			btn_text.set('static')
			self.custom_vals.append(value)
			self.body_text.window_create(tk.INSERT, window=button)

		elif val == 'int':
			btn_text = tk.StringVar()
			button = tk.Button(self.body_text, textvariable=btn_text)
			value = RandomRangeValue(0, 10,  button, btn_text, self.custom_val_veiwer)
			button.configure(command=lambda v=value: self.veiw_custom_val(None, val=v))
			btn_text.set('range [1-10]')
			self.custom_vals.append(value)
			self.body_text.window_create(tk.INSERT, window=button)

		elif val == 'list':
			btn_text = tk.StringVar()
			button = tk.Button(self.body_text, textvariable=btn_text)
			value = RandomFromListValue(['a', 'b', 'c'], button, btn_text, self.custom_val_veiwer)
			button.configure(command=lambda v=value: self.veiw_custom_val(None, val=v))
			btn_text.set('list')
			self.custom_vals.append(value)
			self.body_text.window_create(tk.INSERT, window=button)

		elif val == 'regex':
			btn_text = tk.StringVar()
			button = tk.Button(self.body_text, textvariable=btn_text)
			value = RandomRegexValue('[0-9]', button, btn_text, self.custom_val_veiwer)
			button.configure(command=lambda v=value: self.veiw_custom_val(None, val=v))
			btn_text.set('(regex) [0-9]')
			self.custom_vals.append(value)
			self.body_text.window_create(tk.INSERT, window=button)


		self.custom_vals_variable.set(self.custom_vals)

	def reload_custom_vals(self):
		new_list = []
		for (key, name, index) in self.body_text.dump("1.0", "end", window=True):
			for var in self.custom_vals:
				if str(var.button) == name:
					new_list.append(var)

		self.custom_vals = new_list[:]
		self.custom_vals_variable.set(self.custom_vals)

	def compile_body(self):
		raw = self.body_text.get("1.0",tk.END)
		windows = self.body_text.dump("1.0", "end", window=True)

		if len(windows) <= 0:
			return raw

		lines = raw.split('\n')
		windows.sort(key=lambda x:int(x[2].split('.')[0]) * 1000 + int(x[2].split('.')[1]))
		ordered_vals = []
		for (key, name, index) in windows:
			for val in self.custom_vals:
				if str(val.button) == name:
					row = int(index.split('.')[0]) - 1
					char = int(index.split('.')[1])
					lines[row] = lines[row][:char] + '\0' + lines[row][char:]
					ordered_vals.append(val)

		compiled_lines = ''
		for line in lines:
			compiled_lines += line

		body = ''
		for i, line in enumerate(compiled_lines.split('\0')[:-1]):
			body += line
			body += ordered_vals[i].value()

		body += compiled_lines.split('\0')[-1]

		return body

	def compile_headers(self):
		return dict(self.request.headers)

	def compile_request(self):
		headers = ''
		for (k, v) in self.compile_headers().items():
			headers += k
			headers += ': '
			headers += v
			headers += '\n'

		text = ''
		text += self.request.method
		text += ' '
		text += self.request.url
		text += '\n\n'
		text += headers
		text += '\n'
		text += self.compile_body()

		self.compiled_request_veiwer_text.set(text)

	def make_headers_table(self, request):
		self.headers_temp_frame.destroy()
		self.headers_temp_frame = tk.Frame(self.headers_frame)
		self.headers_temp_frame.pack(side=tk.TOP)

		self.custom_headers = []

		def update_headers(request):
			if self.custom_headers != []:
				request.headers = Headers()

				for key, value in self.custom_headers:
					if key.get != "":
						request.headers[key.get()] = value.get()

		def new_row(request):
			update_headers(request)
			request.headers[""] = ""
			return request

		def delete_row(request, key):
			update_headers(request)
			print(key)
			del request.headers[key]
			return request

		for i, key in enumerate(dict(request.headers).keys()):
			key_entry = tk.Entry(self.headers_temp_frame, relief=tk.RIDGE)
			key_entry.grid(row=i, column=0, sticky=tk.NSEW)
			key_entry.insert(tk.END, key)

			value_entry = tk.Entry(self.headers_temp_frame, relief=tk.RIDGE)
			value_entry.grid(row=i, column=1, sticky=tk.NSEW)
			value_entry.insert(tk.END, dict(request.headers)[key])

			value_entry.bind("<FocusOut>", lambda evt: update_headers(request))
			key_entry.bind("<FocusOut>", lambda evt: update_headers(request))

			tk.Button(
					self.headers_temp_frame, text="delete",
					command=lambda k=key: self.make_headers_table(delete_row(request, k))
			).grid(row=i, column=2)

			self.custom_headers.append((key_entry, value_entry))

		tk.Button(self.headers_temp_frame, text="Add Header",
				  command=lambda: self.make_headers_table(new_row(request))
				  ).grid(row=len(dict(request.headers).keys()), column=2)
