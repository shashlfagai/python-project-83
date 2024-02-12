from flask import Flask

app = Flask(__name__)

@app.route('/')
def say_hello():
    return 'Hello pizduk'

if __name__ == 'main':
    app.run()
