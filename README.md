# dtu-02221-distributed-systems


BikeCoin:
---------------------------------------
* Jeff Gyldenbrand, s202790
* Martin Sander, s202782
* Rasmus Hjorth, s175120
* Mathias Hansen, s175112

Installation & run guide:

In order to run the Proof of Concept application it is required that the user has installed Python with version 3.8 or later. It is also necessary that the user has installed the web application framework `Flask` with version 2 or later. With the required installations in place it is now possible to run the program. This is done with 4 simple steps that includes running the following commands from the root of the project.

Start the centralized wallet (available on port 5003):
```
python3 BikeCoin/wallet.py
```
Start up the three mining nodes using:
```
python3 BikeCoin/node.py <miner_id_1> <port_1>
python3 BikeCoin/node.py <miner_id_2> <port_2>
python3 BikeCoin/node.py <miner_id_3> <port_3>
```
In our example we have used the following input variables but these can be modified if needed

|  Node |          Miner-ID          | Port |
| ----- | -------------------------- | ---- |
|   1   | Niels Christian The Miner  | 5002 |
|   2   | Bubber The Miner           | 5001 |
|   2   | Bubber The Miner           | 5000 |

If any of the values are changed the Postman test script will
no longer be fully functional since it uses these values to perform
requests and validate their responses.

 Connect the nodes using:
 ```
 ./BikeCoin/connect_nodes.sh
 ```

