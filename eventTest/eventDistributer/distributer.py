from pubsub import pub
from flask import Flask
from flask import request
from flask.ext.cors import CORS
import json
import requests
app = Flask(__name__)
cors = CORS(app)

shopSubscriberList = {}

@app.route("/")
def hello():
    return "Event Distributer"

@app.route('/deliveryReady', methods=['POST'])
def deliveryReady():
    error = None
    if request.method == 'POST':
		type = 'deliveryReady'
        shopID = request.form['shopID'];
		orderID = request.form['orderID'];
		order = request.form['order'];
		address = request.form['address'];
		cost = request.form['cost'];

        print 'Publishing Event for deliveryReady'
		topic = 'shop.'+shopID
		eventInfo = {'type': type, 'topic': topic, shopID': shopID, 'orderID': orderID, 'order': shopID, 'address': shopID, 'cost': shopID}
        pub.sendMessage(topic, arg1=eventInfo, arg2=shopID)

        return json.dumps({'success': True})
    else:
        error = 'No shopID'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return json.dumps({'success': False, 'error': error})

@app.route('/subscribeShop', methods=['POST'])
def subscribeShop():
    error = None
    if request.method == 'POST':
        shopID = request.form['shopID'];
        handlerURL = request.form['handlerURL'];

        # subscribe to all shops if shopID is empty
        if not shopID:
            error = 'No shopID'
            return json.dumps({'success': True, 'error': error})
        else:
            if shopID not in shopSubscriberList:
                shopSubscriberList[shopID] = []
            if handlerURL not in shopSubscriberList[shopID]:
                shopSubscriberList[shopID].append(handlerURL);

            pub.subscribe(shopListener, 'shop.'+shopID)
            print 'Subscribed to events for shop '+shopID
        return json.dumps({'success': True})
    else:
        error = 'Something else went wrong'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return json.dumps({'success': False, 'error': error})

def shopListener(arg1, arg2):
    if arg2 in shopSubscriberList:
        for subscriberURL in shopSubscriberList[arg2]:
            payload = {'eventInfo': arg1, 'shopID': arg2}
            r = requests.post(subscriberURL, data=json.dumps(payload))

if __name__ == "__main__":
    app.debug = True
    app.run(port=5000)