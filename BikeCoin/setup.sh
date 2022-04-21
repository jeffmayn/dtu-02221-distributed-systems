#!/bin/bash
curl http://127.0.0.1:5000/get_chain 
curl -X POST http://127.0.0.1:5000/add_items_to_dealer -H 'Content-Type: application/json' -d '{"wallet_id": "The Dealer", "items": ["asd98", "aakjsad", "zxzxc"]}'
curl -X POST http://127.0.0.1:5000/add_transaction -H 'Content-Type: application/json' -d '{"sender": "martin", "receiver": "jeff", "data": "mbhghfgx" }'
curl -X POST http://127.0.0.1:5000/add_transaction -H 'Content-Type: application/json' -d '{"sender": "rasmus", "receiver": "jeff", "data": "uytrytd" }'
curl http://127.0.0.1:5000/mine_block
curl -X POST http://127.0.0.1:5000/add_transaction -H 'Content-Type: application/json' -d '{"sender": "jeff", "receiver": "mathias", "data": "1q2w3e" }'
curl -X POST http://127.0.0.1:5000/add_transaction -H 'Content-Type: application/json' -d '{"sender": "mathias", "receiver": "martin", "data": "mnbvfg" }'
curl http://127.0.0.1:5000/mine_block
curl http://127.0.0.1:5000/get_chain 
