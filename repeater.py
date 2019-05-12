import tkinter as tk
import requests
from tkinter import ttk
from mitmproxy.net.http.headers import Headers
from random_vals import RandomFromListValue, RandomRangeValue, StaticValue, RandomRegexValue

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

		compiled_request_frame = ttk.Labelframe(settings_frame, text='compiled request')
		compiled_request_frame.pack()

		self.compiled_request_veiwer = tk.Text(compiled_request_frame, state=tk.DISABLED)
		self.compiled_request_veiwer.pack()

		tk.Button(settings_frame, text='veiw sample request',command=self.compile_request).pack()
		tk.Button(settings_frame, text='send one', command=lambda: self.send(times=1)).pack()

		self.headers_temp_frame = tk.Frame(self.headers_frame)
		self.headers_temp_frame.pack()

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

		self.make_headers_table(request)
		self.body_text.insert(tk.END, request.text)

		self.custom_headers = []

	def send(self, times=None):
		headers = self.compile_headers()
		body = self.compile_body()
		if times is not None:
			for i in range(times):
				if self.request.method == 'POST':
					response = requests.post(self.request.url, headers=headers, data=body)

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
		self.compiled_request_veiwer.config(state=tk.NORMAL)
		self.compiled_request_veiwer.delete('1.0', tk.END)

		headers = ''
		for (k, v) in self.compile_headers().items():
			headers += k
			headers += ': '
			headers += v
			headers += '\n'

		self.compiled_request_veiwer.insert(tk.END, headers)
		self.compiled_request_veiwer.insert(tk.END, '\n')
		self.compiled_request_veiwer.insert(tk.END, self.compile_body())
		self.compiled_request_veiwer.config(state=tk.DISABLED)

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
