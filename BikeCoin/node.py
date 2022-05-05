from re import S
from flask import Flask, jsonify, request
from uuid import uuid4
from chain import Blockchain
from wallet import Wallet
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import sys

# web app
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# TODO: add login with username when starting node. Change receiver of mining reward to logged in user


# creating an address for the node on port 5000
#node_address = str(uuid4()).replace('-', '')

# Scheduler
scheduler = BackgroundScheduler(daemon=True)

# create a blockchain
blockchain = Blockchain()

# create wallets
wallets = [
    Wallet("Buyer One", []), 
    Wallet("Buyer Two", []), 
    Wallet("Buyer Three", []), 
    Wallet("Thief", []), 
    Wallet("Dealer", [], type='dealer'), 
]

# mining a blockchain
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    if(len(blockchain.pendingTransactions) == 0):
        return jsonify("No pending transactions"), 418

    for t in blockchain.pendingTransactions:
        sWallet = next((w for w in wallets if w.id == t['sender']), None)
        rWallet = next((w for w in wallets if w.id == t['receiver']), None)

        if(rWallet.type != 'dealer'):
            sWallet.remove_item(t['data'])
            rWallet.add_item(t['data'])

    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_pendingTransaction(sender = 'Gaveboden A/S', receiver = 'Jeff, The Master of Mining', data = blockchain.miningReward)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message' : 'Tillykke, du har lige minet en block!', 
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transactions' : block['transactions']
                }

    # update neighbour nodes
    for node in blockchain.nodes:
        requests.get(f'http://{node}/notify')

    return jsonify(response), 200

# get the full blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200

# check if blockchain valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message' : 'The blockchain is valid'}
    else:
        response = {'message' : 'The blockchain is not valid'}
    return jsonify(response), 200  

# adding a new transaction to the blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'data']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    
    sWallet = next((w for w in wallets if w.id == json['sender']), None)
    if(sWallet == None):
        return jsonify("Sender does not exist"), 418

    rWallet = next((w for w in wallets if w.id == json['receiver']), None)
    if(rWallet == None):
        return jsonify("Receiver does not exist"), 418
    
    if(not sWallet.contains_item(json['data']) and sWallet.type != 'dealer'):
        return jsonify("Sender does not own item"), 418

    status = json['status'] if 'status' in json else 'legit'
    index = blockchain.add_pendingTransaction(json['sender'], json['receiver'], json['data'], status)
    response = {'message' : f'This transaction will be added to Block {index}'}
    return jsonify(response), 201 
    
# decentralize our blockchain

# connection new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    
    if nodes is None:
        return "No node", 400
    
    for node in nodes:
        blockchain.add_node(node)
        
    response = {'message' :'All the nodes are now connected. The bubbercoin now contains the following nodes' ,
                'total_nodes' : list(blockchain.nodes)
                }
    return jsonify(response), 201 

# replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message' : 'The nodes had different chains so the chain was replaced by the longest one',
                    'new_chain' : blockchain.chain
                    }
    else:
        response = {'message' : 'All good. The chain is the longest one',
                    'chain' : blockchain.chain}
    return jsonify(response), 200 

@app.route('/get_transactions', methods = ['GET'])
def get_transactions():
    return jsonify(blockchain.pendingTransactions), 200 

@app.route('/get_wallets', methods = ['GET'])
def get_wallets():
    for w in wallets:
        print("Wallet: " + w.id + " Items: ")
        print(w.items)
    return jsonify([w.__dict__ for w in wallets]), 200 

@app.route('/add_items_to_dealer', methods = ['POST'])
def add_items_to_dealer():
    json = request.get_json()
    items = json['items']
    wallet_id = json['wallet_id']
    
    if items is None :
        return "No items", 400

    if wallet_id is None :
        return "No wallet", 400
    
    
    wallet = next((w for w in wallets if w.id == wallet_id), None)

    if wallet is None:
        return "Wallet does not exist", 400

    if wallet.type != 'dealer':
        return "Wallet is invalid", 400
    
    response = 'Items has been added to wallet. Items have been added to the block with id: '
    for item in items:
        wallet.add_item(item)
        index = blockchain.add_pendingTransaction('-', 'Dealer', item, 'legit')
        

    return jsonify(response + str(index)), 200

@app.route('/verify_owner', methods = ['GET'])
def verify_owner():
    json = request.get_json()
    owner = json['owner']
    frame_number = json['frame_number']

    t_all = []

    for block in blockchain.chain:
        for transaction in block['transactions']:
            if(transaction['data'] == frame_number):
                t_all.append(transaction)

    date_format = '%Y-%m-%d %H:%M:%S:%f'

    res = sorted(t_all, key=lambda t: datetime.strptime(t['timestamp'], date_format))
    if len(res) <= 0:
        return jsonify("No results found"), 200 
    elif res[-1]['status'] == 'stolen': 
        return jsonify("OOOOOH SHIIIIIT! This bike is reported stolen")
    elif res[-1]['receiver'] == owner:
        return jsonify("Owner is verified!"), 200 
    else:
        return jsonify("NOOOOOOOO! The suggested owner can not be verified as the real owner"), 200 

@app.route('/notify', methods = ['GET'])
def notify():

    scheduler.add_job(scheduled_updated)
    scheduler.start()

    return jsonify("All good"), 200 

# Background task
def scheduled_updated():
    print("Updating chain")
    global scheduler

    blockchain.replace_chain()

# running the app
port = 5000
if(sys.argv[1] != None):
    port = sys.argv[1]

app.run(host = '0.0.0.0', port = port)