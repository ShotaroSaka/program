import overpy
import csv
import osmnx as ox


def fetch_result(key, tag):
    api = overpy.Overpass()
    query = (
        'node(around:2000, 34.908913, 135.185743)["{key}"="{tag}"];\n'
        'out;'
    ).format(key=key, tag=tag)

    print('Fetch query...')
    result = api.query(query)

    print("success")

    return result

def fetch_result_2(key):
    api = overpy.Overpass()
    query = (
        'node(around:2000, 34.908913, 135.185743)["{key}"];\n'
        'out;'
    ).format(key=key)

    print('Fetch query...')
    result = api.query(query)

    print("success")

    return result


key = "shop"
tag = "supermarket"
result = fetch_result(key, tag)

shop_database = []
for node in result.nodes:
    point = (float(node.lat), float(node.lon))
    print(point)
    shop_database.append([float(node.lat), float(node.lon)])

# key1 = "shop"
# tag1 = "convenience"

# key2 = "amenity"
# tag2 = "parking"

# key3 = "shop"
# tag3 = "supermarket"

# result1 = fetch_result(key1, tag1)
# result2 = fetch_result(key2, tag2)
# result3 = fetch_result(key3, tag3)


# ショップをshop_databaseに入れる
# shop_database = []
# for i in [result1,result2,result3]:
#     print("a")
#     for node in i.nodes:
#         point = (float(node.lat), float(node.lon))
#         print(point)
#         shop_database.append([float(node.id), float(node.lat), float(node.lon)])

print(shop_database)
with open("Sanda_shop_list_all.csv", "w", newline="") as f:
    writer = csv.writer(f)
    for data in shop_database:
        writer.writerow(data)
f.close()








        
