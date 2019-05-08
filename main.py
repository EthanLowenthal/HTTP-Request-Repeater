from mitmproxy import proxy, options
# from mitmproxy.net.http.headers import Headers
from mitmproxy.net.http.http1.assemble import assemble_request, assemble_request_head, assemble_response_head #, assemble_response
from mitmproxy.tools.dump import DumpMaster
import tkinter as tk
from tkinter import ttk
import requests
import queue
import datetime
from threading import Thread, Lock
import sys
from repeater import Repeater
from mitm import start_mitm, Addon


class Window:
    def __init__(self, queue, lock, addon):
        self.window = tk.Tk()
        self.window.geometry("800x600")
        self.window.title("Heccin' Tool")

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=1)
        intercept_frame = tk.Frame(notebook)
        history_frame = tk.Frame(notebook)
        notebook.add(intercept_frame, text='Interceptor')
        notebook.add(history_frame, text='HTTP History')

        controls = tk.Frame(intercept_frame)

        self.intercept = tk.IntVar()
        tk.Checkbutton(controls, text="intercept", command=self.toggle_intercept, variable=self.intercept).pack(side=tk.LEFT)

        self.forward_button = tk.Button(controls, text="forward", command=self.forward_request, state=tk.DISABLED)
        self.forward_button.pack(side=tk.RIGHT)

        self.drop_button = tk.Button(controls, text="drop", command=self.drop_request, state=tk.DISABLED)
        self.drop_button.pack(side=tk.RIGHT)

        controls.pack()

        self.intercept_veiwer = tk.Text(intercept_frame, state=tk.DISABLED)
        self.intercept_veiwer.pack(fill=tk.BOTH, expand=1)

        self.history = []

        self.history_variable = tk.Variable(value=self.history)

        self.history_list = tk.Listbox(history_frame, listvariable=self.history_variable)
        self.history_list.pack(fill=tk.BOTH, expand=1)
        self.history_list.bind("<Double-Button-1>", self.veiw_flow)

        request_notebook = ttk.Notebook(history_frame)
        request_notebook.pack(fill=tk.BOTH, expand=1)
        request_frame = tk.Frame(request_notebook)
        response_frame = tk.Frame(request_notebook)
        request_notebook.add(request_frame, text='Request')
        request_notebook.add(response_frame, text='Response')

        self.send_to_repeater_button = tk.Button(request_frame, text="Send to Repeater", command=self.send_to_repeater)
        self.send_to_repeater_button.pack()

        self.request_veiwer = tk.Text(request_frame, state=tk.DISABLED)
        self.request_veiwer.pack(fill=tk.BOTH, expand=1)

        self.response_veiwer = tk.Text(response_frame, state=tk.DISABLED)
        self.response_veiwer.pack(fill=tk.BOTH, expand=1)


        self.queue = queue
        self.lock = lock
        self.addon = addon
        self.repeating_flow = None

        self.byte_to_string = lambda s: str(s)[2:-1].replace('\\r', '').replace('\\n', '\n')


        if 'test' in sys.argv:
            import test
            Thread(target=test.start).start()
            tk.Button(intercept_frame, text="Test Request", command=self.test_post).pack()

    def test_post(self):
        requests.post('http://127.0.0.1:5000/post', data={'key': 'value'})

    def run(self):
        self.get_next_request()
        self.window.mainloop()

    def veiw_flow(self, selection):
        flow = self.history[self.history_list.curselection()[0]]
        self.request_veiwer.config(state=tk.NORMAL)
        self.request_veiwer.delete('1.0', tk.END)

        self.response_veiwer.config(state=tk.NORMAL)
        self.response_veiwer.delete('1.0', tk.END)

        if flow.request is not None:
            request = self.byte_to_string(assemble_request_head(flow.request))
            request += flow.request.text
            self.request_veiwer.insert(tk.END, request)
        else:
            self.request_veiwer.insert(tk.END, 'NO REQUEST')

        if flow.response is not None:
            response = self.byte_to_string(assemble_response_head(flow.response))
            response += flow.response.text
            self.response_veiwer.insert(tk.END, response)
        else:
            self.response_veiwer.insert(tk.END, 'NO RESPONSE')

        self.request_veiwer.config(state=tk.DISABLED)
        self.response_veiwer.config(state=tk.DISABLED)

    def get_next_request(self):
        self.intercept_veiwer.config(state=tk.NORMAL)

        if self.intercept.get():
            self.intercept_veiwer.delete('1.0', tk.END)
            with self.lock:
                if len(self.addon.intercepted_flows) > 0:
                    data = self.addon.intercepted_flows[0]

                    self.history.append(data)

                    self.intercept_veiwer.insert(tk.END, self.byte_to_string(assemble_request(data.request)))

                    self.forward_button.config(state="normal")
                    self.drop_button.config(state="normal")

                else:

                    self.intercept_veiwer.insert(tk.END, "")

                    self.forward_button.config(state="disabled")
                    self.drop_button.config(state="disabled")

        else:
            while not self.queue.empty():
                data = self.queue.get(True, 0.5)
                self.history.append(data)

                self.intercept_veiwer.delete('1.0', tk.END)
                self.intercept_veiwer.insert(tk.END, self.byte_to_string(assemble_request(data.request)))

                self.forward_button.config(state="disabled")
                self.drop_button.config(state="disabled")

        self.intercept_veiwer.config(state=tk.DISABLED)

        self.update_history()
        self.window.after(1000, self.get_next_request)

    def forward_request(self):
        with self.lock:
            flow = self.addon.intercepted_flows[0]
            flow.resume()
            self.addon.queue.put(flow)
            self.addon.intercepted_flows.pop(0)

    def drop_request(self):
        with self.lock:
            flow = self.addon.intercepted_flows[0]
            if flow.response is None:
                flow.dropped = True
            else:
                flow.response.content = b""
            flow.resume()
            self.addon.queue.put(flow)
            self.addon.intercepted_flows.pop(0)

    def toggle_intercept(self):
        with self.lock:
            if not self.addon.intercept:
                self.addon.intercept = True

            else:
                self.addon.intercept = False
                for flow in self.addon.intercepted_flows:
                    flow.resume()

                    self.addon.queue.put(flow)

    def update_history(self):
        history_formatted = []
        for flow in self.history:

            if flow.request is not None:
                timestamp = datetime.datetime.utcfromtimestamp(flow.request.timestamp_start).strftime("%x %X")
                method = flow.request.method
                host = flow.request.host
            else:
                timestamp = "none"
                method = "none"
                host = "no request"

            if flow.response is not None:
                status = flow.response.status_code
            else:
                status = "none"

            string = "{} - {} {} - status {}".format(timestamp, method, host, status)
            history_formatted.append(string)

        self.history_variable.set(history_formatted)


    def send_to_repeater(self):
        request = self.history[self.history_list.curselection()[0]].request
        Repeater(self.window, request)


    def repeat(self):
        if self.repeating_flow.request is None:
            return

        url = self.repeating_flow.request.host_header + self.repeating_flow.request.path
        with self.lock:
            self.addon.repeating = url

        requests.post(url, headers=self.make_repeating_headers(), data=self.make_repeating_data())

        self.addon.repeating = None

    def make_repeating_headers(self):
        pass

    def make_repeating_data(self):
        pass



def start():
    lock = Lock()
    q = queue.Queue()

    addon = Addon(q, lock)
    window = Window(q, lock, addon)

    opts = options.Options(listen_host='0.0.0.0', listen_port=8080)
    pconf = proxy.config.ProxyConfig(opts)
    master = DumpMaster(opts)
    master.server = proxy.server.ProxyServer(pconf)
    master.addons.add(addon)

    mitm_thread = Thread(target=start_mitm, args=(master,))
    mitm_thread.daemon = True
    mitm_thread.start()

    window.run()


start()
