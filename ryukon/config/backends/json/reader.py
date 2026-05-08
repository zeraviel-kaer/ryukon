import orjson

class JsonBackend:
    def __init__(self, path: str):
        self.path = path

    def read(self):
        with open(self.path, "rb") as f:
            return orjson.loads(f.read())
        
    def write(self, data: dict):
        with open(self.path, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))