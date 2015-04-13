from flask import Flask
from flask import render_template
from flask.ext.cors import CORS
app = Flask(__name__)
cors = CORS(app)

@app.route("/")
def hello():
    return "Welcome Drivers!"


@app.route('/subscribeShop/')
@app.route('/subscribeShop/<shopID>')
def subscribeShop(shopID=None):
    return render_template('subscribeShop.html', shopID=shopID)

if __name__ == "__main__":
    app.debug = True
    app.run(port=5002)