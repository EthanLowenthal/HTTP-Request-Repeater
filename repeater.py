import tkinter as tk
from tkinter import ttk
from random_vals import RandomFromListValue, RandomRangeValue, StaticValue

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

		self.headers_temp_frame = tk.Frame(self.headers_frame)
		self.headers_temp_frame.pack()

		controls_frame = ttk.Labelframe(self.headers_frame, text='controls')
		controls_frame.pack(side=tk.BOTTOM, fill=tk.X)
		temp_frame = tk.Frame(controls_frame)
		temp_frame.pack()
		tk.Button(temp_frame, text='static value').pack(side=tk.LEFT)
		tk.Button(temp_frame, text='random integer').pack(side=tk.LEFT)
		tk.Button(temp_frame, text='random value from list').pack(side=tk.LEFT)
		tk.Button(temp_frame, text='random regex').pack(side=tk.LEFT)

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

		self.custom_vals_list = tk.Listbox(val_temp_frame, listvariable=self.custom_vals_variable)
		self.custom_vals_list.pack(fill=tk.BOTH, expand=1, side=tk.TOP)
		self.custom_vals_list.bind("<Double-Button-1>", self.veiw_custom_val)

		self.custom_val_veiwer = tk.Frame(val_temp_frame)
		self.custom_val_veiwer.pack(side=tk.BOTTOM)

		self.body_text.delete('1.0', tk.END)

		self.make_headers_table(request)
		self.body_text.insert(tk.END, request.text)

		self.custom_headers = []

	def veiw_custom_val(self, evt):
		for slave in self.custom_val_veiwer.pack_slaves():
			slave.pack_forget()
		custom_val = self.custom_vals[self.custom_vals_list.curselection()[0]]
		custom_val.display()

	def add_custom_value_to_body(self, val):
		if val == 'static':
			btn_text = tk.StringVar()
			button = tk.Button(self.body_text, textvariable=btn_text)
			btn_text.set('static')
			self.custom_vals.append(StaticValue('static', btn_text, self.custom_val_veiwer))
			self.body_text.window_create(tk.INSERT, window=button)

		elif val == 'int':
			btn_text = tk.StringVar()
			button = tk.Button(self.body_text, textvariable=btn_text)
			btn_text.set('range [1-10]')
			self.custom_vals.append(RandomRangeValue(0, 10, btn_text, self.custom_val_veiwer))
			self.body_text.window_create(tk.INSERT, window=button)

		elif val == 'list':
			btn_text = tk.StringVar()
			button = tk.Button(self.body_text, textvariable=btn_text)
			btn_text.set('list')
			self.custom_vals.append(RandomFromListValue(['a', 'b', 'c'], btn_text, self.custom_val_veiwer))
			self.body_text.window_create(tk.INSERT, window=button)

		elif val == 'regex':
			button = tk.Button(self.body_text, text='random regex')
			self.body_text.window_create(tk.INSERT, window=button)

		self.custom_vals_variable.set(self.custom_vals)

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
