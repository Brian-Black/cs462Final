from flask import Flask
from flask import render_template
from flask.ext.cors import CORS
import uuid
app = Flask(__name__)
cors = CORS(app)

@app.route("/")
def index():
    return "Welcome to the Flower Shop!"

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/delivery/')
def delivery():
	orderID = uuid.uuid1()
    return render_template('delivery.html', orderID = orderID)

if __name__ == "__main__":
	app.debug = True
	app.run(port=5001)