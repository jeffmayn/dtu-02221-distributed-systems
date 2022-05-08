from re import S
from flask import Flask, jsonify, request
from uuid import uuid4
from chain import Blockchain
import requests
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import sys

# web app
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
wallet_url = "127.0.0.1:5003"
headers = {"Content-Type": "application/json; charset=utf-8"}

# creating an address for the node on port 5000
#node_address = str(uuid4()).replace('-', '')

# Scheduler
scheduler = BackgroundScheduler(daemon=True)

# create a blockchain
blockchain = Blockchain()

miner_wallet_id = ''

# mining a blockchain
@app.route('/mine_block', methods = ['GET'])
def mine_block():

    if(len(blockchain.pendingTransactions) == 0):
        return jsonify("No pending transactions"), 418

    response = requests.post(f'http://{wallet_url}/transfer_items', headers=headers, json={"pendingTransactions": blockchain.pendingTransactions})

    if(response.status_code != 200):
        return response.text, response.status_code

    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_pendingTransaction(sender = 'Chain Insurance Ltd.', receiver = miner_wallet_id, data = blockchain.miningReward, timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')))
    block = blockchain.create_block(proof, previous_hash)

    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if(not is_valid):
        return jsonify("The chain is invalid. Block is not added to chain"), 418


    response = {'message' : 'Tillykke, du har lige minet en block!', 
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transactions' : block['transactions']
                }

    # update neighbour nodes
    for node in blockchain.nodes:
        requests.post(f'http://{node}/notify', headers=headers, json=block)

    return jsonify(response), 200

# get the full blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200

 # retrieves pending transactions
@app.route('/get_pending_transactions', methods = ['GET'])
def get_pending_transactions():
    response = {'transactions' : blockchain.pendingTransactions}
    blockchain.pendingTransactions = []
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
    
    response = requests.get(f'http://{wallet_url}/validate_from_and_to_wallets', json=json)
    if(response.status_code != 200):
        return response.text, response.status_code

    status = json['status'] if 'status' in json else 'legit'

    transaction = {
        'sender': json['sender'], 
        'receiver': json['receiver'], 
        'data': json['data'], 
        'timestamp': str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')), 
        'status': status
    }

    index = blockchain.add_pendingTransaction(transaction['sender'], transaction['receiver'], transaction['data'], transaction['timestamp'],  transaction['status'])
    response = {'message' : f'This transaction will be added to Block {index}'}

    # notify network - add transactions
    for node in blockchain.nodes:
        print(requests.post(f'http://{node}/broadcast_transactions', headers=headers, json=[transaction]).text)

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
        
    scheduler.add_job(scheduled_updated, 'interval', seconds=30)
    scheduler.start()

    response = {'message' :'All the nodes are now connected. The bubbercoin now contains the following nodes' ,
                'total_nodes' : list(blockchain.nodes)
                }
    return jsonify(response), 200 

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

@app.route('/add_items_to_dealer', methods = ['POST'])
def add_items_to_dealer():
    json = request.get_json()
    items = json['items']
    wallet_id = json['wallet_id']
    
    if items is None :
        return "No items", 400

    if wallet_id is None :
        return "No wallet", 400

    response = requests.post(f'http://{wallet_url}/validate_dealer', headers=headers, json={"wallet_id": wallet_id})
    if(response.status_code != 200):
        return response.text, response.status_code

    response = 'Items has been added to wallet. Items have been added to the block with id: '
    transactions = []
    for item in items:
        t = {
            'sender' : "-",
            'receiver' : "Dealer",
            'data' : item,
            'timestamp': str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')),
            'status': "legit"
        }
        index = blockchain.add_pendingTransaction(t['sender'], t['receiver'], t['data'], t['timestamp'], t['status'])
        transactions.append(t)           

    # notify network - add transactions
    for node in blockchain.nodes:
        print(requests.post(f'http://{node}/broadcast_transactions', headers=headers, json=transactions).text)

    return jsonify(response + str(index)), 200

@app.route('/broadcast_transactions', methods = ['POST'])
def broadcast_transactions():
    transactions = request.get_json()
    index = "-"
    for t in transactions:
        index = blockchain.add_pendingTransaction(t['sender'], t['receiver'], t['data'], t['timestamp'], t['status'])

    response = 'Items has been added to wallet. Items have been added to the block with id: '

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

    res = sorted(t_all, key=lambda t: datetime.datetime.strptime(t['timestamp'], date_format))
    if len(res) <= 0:
        return jsonify("No results found"), 200 
    elif res[-1]['status'] == 'stolen': 
        return jsonify("OOOOOH SHIIIIIT! This bike is reported stolen")
    elif res[-1]['receiver'] == owner:
        return jsonify("Owner is verified!"), 200 
    else:
        return jsonify("NOOOOOOOO! The suggested owner can not be verified as the real owner"), 200 


@app.route('/provenance_history', methods = ['GET'])
def get_provenance_history():
    json = request.get_json()
    frame_number = json['frame_number']

    provenance_history = []

    for block in blockchain.chain:
        for transaction in block['transactions']:
            if(transaction['data'] == frame_number):
                provenance_history.append(transaction)

    date_format = '%Y-%m-%d %H:%M:%S:%f'
    sorted_history = sorted(provenance_history, key=lambda t: datetime.datetime.strptime(t['timestamp'], date_format), reverse=True)
    return jsonify(sorted_history), 200 


@app.route('/wallet_balance', methods = ['GET'])
def miner_wallet_balance():
    json = request.get_json()
    wallet_id = json['wallet_id']

    balance = 0
    for block in blockchain.chain:
        for transaction in block['transactions']:
            if(transaction['receiver'] == wallet_id):
                data = transaction['data']
                balance += float(data) if str(data).isnumeric() else 0

    account = { "balance": balance }
    return jsonify(account), 200 

@app.route('/notify', methods = ['POST'])
def notify():
    block = request.get_json()

    blockchain.chain.append(block)
    is_valid = blockchain.is_chain_valid(blockchain.chain)

    t_remove = []
    if(is_valid):
        for t in block['transactions']:
            for tp in blockchain.pendingTransactions:
                if(blockchain.hash(t) == blockchain.hash(tp)):
                    t_remove.append(tp)

        for t in t_remove:
            blockchain.pendingTransactions.remove(t)
            
        return jsonify("All good"), 200 
    else:
        blockchain.chain.remove(block)
        return jsonify("Block can not be verified"), 418 


# Background task
def scheduled_updated():
    print("Updating chain")
    global scheduler

    blockchain.replace_chain()


# running the app
port = 5000
if(sys.argv[1] != None):
    port = sys.argv[1]

miner_wallet_id = sys.argv[2]

app.run(host = '0.0.0.0', port = port)