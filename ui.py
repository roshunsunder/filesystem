from indexer import Indexer
from query import QueryDriver
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
q = QueryDriver()
q.load_from_disk("faiss_index")

@app.route('/query', methods=['POST'])
def query():
    global q
    string = request.json['query']
    res = q.query(string)
    return {"result" : res}

if __name__ == "__main__":
    app.run(debug=True, port=8686)