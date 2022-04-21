#!/bin/bash
curl -X POST http://127.0.0.1:5000/connect_node -H 'Content-Type: application/json' -d '{"nodes": ["http://127.0.0.1:5001","http://127.0.0.1:5002"]}'
curl -X POST http://127.0.0.1:5001/connect_node -H 'Content-Type: application/json' -d '{"nodes": ["http://127.0.0.1:5000","http://127.0.0.1:5002"]}'
curl -X POST http://127.0.0.1:5002/connect_node -H 'Content-Type: application/json' -d '{"nodes": ["http://127.0.0.1:5001","http://127.0.0.1:5000"]}'
