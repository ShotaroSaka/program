from datetime import datetime

import dill
import overpy


def input_node_info():
    key = input('Input node key:')
    tag = input('Input tag of key:')
    return key, tag

        
def fetch_result(key, tag):
    api = overpy.Overpass()
    query = (
        'area["name"~"三田"];\n'
        'node(area)["{key}"="{tag}"];\n'
        'out;'
    ).format(key=key, tag=tag)
    print('Fetch query...')
    result = api.query(query)

    for node in result.nodes:
        print(node.tags.get())
        
        


def main():
    key, tag = input_node_info()
    fetch_result(key, tag)


if __name__ == "__main__":
    main()
