import json
from flask import Flask, jsonify, request

class Wallet:
    
    def __init__(self, id, items = [], type = "customer"):
        self.id = id
        self.items = items
        self.type = type

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, item):
        self.items.remove(item)

    def get_items(self):
        return self.items

    def contains_item(self, item):
        return item in self.items

    def get_id(self):
        return self.id

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


# web app
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False


# create wallets
wallets = [
    Wallet("Buyer One", []), 
    Wallet("Buyer Two", []), 
    Wallet("Buyer Three", []), 
    Wallet("Thief", []), 
    Wallet("Dealer", [], type='dealer'), 
    Wallet("Bubber The Miner", [], type="miner"),
    Wallet("Niels Christian The Miner", [], type="miner")

]

@app.route('/get_wallets', methods = ['GET'])
def get_wallets():
    return jsonify([w.__dict__ for w in wallets]), 200 

@app.route('/transfer_items', methods = ['POST'])
def transfer_items():
    json = request.get_json()
    pendingTransactions = json.get('pendingTransactions')

    for t in pendingTransactions:
        sWallet = next((w for w in wallets if w.id == t['sender']), None)
        rWallet = next((w for w in wallets if w.id == t['receiver']), None)

        if(rWallet.type != 'dealer'):
            sWallet.remove_item(t['data'])
            rWallet.add_item(t['data'])

    return jsonify("Items transferred"), 200

@app.route('/validate_from_and_to_wallets', methods = ['GET'])
def validate_from_and_to_wallets():
    json = request.get_json()

    sWallet = next((w for w in wallets if w.id == json['sender']), None)
    if(sWallet == None):
        return jsonify("Sender does not exist"), 418

    rWallet = next((w for w in wallets if w.id == json['receiver']), None)
    if(rWallet == None):
        return jsonify("Receiver does not exist"), 418
    
    if(not sWallet.contains_item(json['data']) and sWallet.type != 'dealer'):
        return jsonify("Sender does not own item"), 418

    return jsonify("All good"), 200

@app.route('/add_items_to_wallet', methods = ['POST'])
def add_items_to_wallet():
    json = request.get_json()
    items = json['items']
    wallet_id = json['wallet_id']

    wallet = next((w for w in wallets if w.id == wallet_id), None)

    if wallet is None:
        return "Wallet does not exist", 400

    if wallet.type != 'dealer':
        return "Wallet is invalid", 400

    for item in items:
        wallet.add_item(item)

    return jsonify([w.__dict__ for w in wallets]), 200 


app.run(host = '0.0.0.0', port = 5003)