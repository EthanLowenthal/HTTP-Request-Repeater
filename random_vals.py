import tkinter as tk
import random

class RandomFromListValue:
	def __init__(self, list, btn_txt, veiwer):
		self.btn_txt = btn_txt
		self.veiwer = veiwer
		self.frame = tk.Frame(self.veiwer)
		self.list = list
		self.entries = []

	def val(self):
		return random.choice(self.list)

	def append(self, val):
		self.list.append(val)
		self.display()

	def pop(self, idx):
		self.list.pop(idx)
		self.display()

	def update(self, evt):
		self.list = []
		for ent in self.entries:
			self.list.append(ent.get())

	def display(self):
		self.frame.pack_forget()
		del self.frame
		self.frame = tk.Frame(self.veiwer)
		self.entries = []
		for i, elem in enumerate(self.list):
			ent = tk.Entry(self.frame)
			ent.insert(tk.END, elem)
			ent.grid(row=i, column=0)
			ent.bind('<KeyRelease>', self.update)

			but = tk.Button(self.frame, text="x", command=lambda idx=i: self.pop(idx))
			but.grid(row=i, column=1)
			self.entries.append(ent)

		tk.Button(self.frame, text="Add Item", command=lambda : self.append("")).grid(row=len(self.list), column=0)
		self.frame.pack()

	def __str__(self):
		return "Random List"


class RandomRangeValue:
	def __init__(self, min, max, btn_txt, veiwer):
		self.btn_txt = btn_txt
		self.veiwer = veiwer
		self.frame = tk.Frame(self.veiwer)

		self.min_entry = tk.Entry(self.frame)
		self.min_entry.pack(side=tk.LEFT)
		self.min_entry.bind('<KeyRelease>', self.update)

		self.max_entry = tk.Entry(self.frame)
		self.max_entry.pack(side=tk.LEFT)
		self.max_entry.bind('<KeyRelease>', self.update)

		self.min = min
		self.max = max

	def val(self):
		return random.randint(int(self.min), int(self.max))

	def set_max(self, val):
		self.min = val

	def set_min(self, val):
		self.max = val

	def update(self, evt):
		self.min = self.min_entry.get()
		self.max = self.max_entry.get()
		self.btn_txt.set("range [{}-{}]".format(self.min, self.max))

	def display(self):
		self.min_entry.delete(0, tk.END)
		self.min_entry.insert(tk.END, self.min)
		self.max_entry.delete(0, tk.END)
		self.max_entry.insert(tk.END, self.max)
		self.frame.pack()

	def __str__(self):
		return "Random Range"


class StaticValue:
	def __init__(self, val, btn_txt, veiwer):
		self.btn_txt = btn_txt
		self.veiwer = veiwer
		self.frame = tk.Frame(self.veiwer)
		self.entry = tk.Entry(self.frame)
		self.entry.pack()
		self.entry.bind('<KeyRelease>', self.update)
		self.val = val

	def val(self):
		return self.val

	def set(self, val):
		self.val = val

	def update(self, evt):
		self.val = self.entry.get()
		self.btn_txt.set(self.val)

	def display(self):
		self.entry.delete(0, tk.END)
		self.entry.insert(tk.END, self.val)
		self.frame.pack()

	def __str__(self):
		return "Static Variable"