from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello World!"

@app.route('/post', methods=['POST'])
def post():
    print('got:')
    print(dict(request.form))
    print()
    return str(dict(request.form))

def start():
    app.run(host='127.0.0.1', port=5000)