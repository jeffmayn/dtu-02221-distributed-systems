import datetime
import hashlib
import json
import requests
from urllib.parse import urlparse



# blockchain
class Blockchain:

    master_node = "127.0.0.1:5000"
    
    def __init__(self):
        self.chain = []
        self.pendingTransactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        self.miningReward = 100
        
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp' : str(datetime.datetime.now()),
                 'proof' : proof,
                 'previous_hash' : previous_hash,
                 'transactions' : self.pendingTransactions
                 }
        self.pendingTransactions = []
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
            
        return new_proof
            
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
           
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    def add_pendingTransaction(self, sender, receiver, data, status = ""):
        self.pendingTransactions.append({
            'sender' : sender,
            'receiver' : receiver,
            'data' : data,
            'timestamp': str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')),
            'status': status
        })
        
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        print("Parsed: ", parsed_url)
        self.nodes.add(parsed_url.netloc)
        print("Nodes: ", self.nodes)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

    def get_pending_transactions(self):
        response = requests.get(f'http://{self.master_node}/get_pending_transactions')
        transactions = response.json()['transactions']
        self.pendingTransactions = transactions

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)