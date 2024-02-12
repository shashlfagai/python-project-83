from flask import Flask

app = Flask(__name__)

if __name__ == 'main':
    app.run()

@app.route('/')
def say_hello():
    return 'Hello pizduk'
