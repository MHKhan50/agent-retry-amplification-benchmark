import json
from benchmark import run

if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
