import overpy
import csv
import osmnx as ox


def fetch_result(key, tag):
    api = overpy.Overpass()
    query = (
        'way(around:1000, 34.908913, 135.185743)["{key}"="{tag}"];\n'
        '(._;>;);'
        'out;'
        
    ).format(key=key, tag=tag)

    print('Fetch query...')
    result = api.query(query)

    print("success")

    return result

key = "amenity"
tag = "parking"

result = fetch_result(key, tag)


parking_database = []
for way in result.ways:
    point = (float(way.nodes[0].lat), float(way.nodes[0].lon))
    print(point)
    parking_database.append([float(way.nodes[0].id), float(way.nodes[0].lat), float(way.nodes[0].lon)])


print(parking_database)
with open("Sanda_parking_list.csv", "w", newline="") as f:
    writer = csv.writer(f)
    for data in parking_database:
        writer.writerow(data)
f.close()















