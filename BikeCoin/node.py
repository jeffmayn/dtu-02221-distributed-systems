from re import S
from flask import Flask, jsonify, request
from uuid import uuid4
from chain import Blockchain
from wallet import Wallet
import json

# web app
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    
# creating an address for the node on port 5000
node_address = str(uuid4()).replace('-', '')



# create a blockchain
blockchain = Blockchain()
wallets = [
    Wallet("jeff", ["1q2w3e", "0p9oi8"]),
    Wallet("martin", ["mbhghfgx"]),
    Wallet("mathias", ["yuytd", "mnbvfg"]),
    Wallet("rasmus", ["uytrytd"]),
]

# mining a blockchain
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    if(len(blockchain.pendingTransactions) == 0):
        return jsonify("No pending transactions"), 418

    for t in blockchain.pendingTransactions:
        sWallet = next((w for w in wallets if w.id == t['sender']), None)
        rWallet = next((w for w in wallets if w.id == t['receiver']), None)

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
    
    if(not sWallet.contains_item(json['data'])):
        return jsonify("Sender does not own item"), 418

    index = blockchain.add_pendingTransaction(json['sender'], json['receiver'], json['data'])
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
    return json.dumps([w.__dict__ for w in wallets]), 200 


# running the app
app.run(host = '0.0.0.0', port = 5000)

                
        