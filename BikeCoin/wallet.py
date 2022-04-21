import json

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
