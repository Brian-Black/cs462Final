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
	
@app.Route('/processEvent/')
def processEvent():
	if request.method == 'POST':
		type = request.form['type']
		switch(type):
			case ('deliveryReady'):
				shopID = request.form['shopID'];
				orderID = request.form['orderID'];
				order = request.form['order'];
				address = request.form['address'];
				cost = request.form['cost']; 
				# add all these to the database for the driver site
				# so they can be displayed on the "available deliveries" page

if __name__ == "__main__":
    app.debug = True
    app.run(port=5002)