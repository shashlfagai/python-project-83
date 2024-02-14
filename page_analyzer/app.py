from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
def page_analyzer():
    return render_template('index.html')


@app.get('/urls')
def analyzed_pages():
    return "It's not ready"


@app.post('/urls')
def analyzing_page():
    return "It's not ready"


if __name__ == '__main__':
    app.run()
