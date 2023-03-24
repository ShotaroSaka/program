import os
from pathlib import Path
import overpy
import folium
import osmnx as ox

def fetch_result(key):
    api = overpy.Overpass()
    query = (
        'area["name"~"三田市"];\n'
         'node(area)["{key}"];\n'
         'out;'
    ).format(key=key)
    print('Fetch query...')
    result = api.query(query)

    print("success")

    return result

key = "shop"

result = fetch_result(key)

parking_database  = []
for node in result.nodes:
    point = (float(node.lat), float(node.lon))
    print(point)
    parking_database.append([float(node.id),float(node.lat), float(node.lon)])


# 対象地域検索クエリ (愛知県名古屋市中村区)
query = "Sanda,Hyogo,Japan"


# 各種出力ファイルパス
outdir_path = Path(query.replace(",", "_"))
os.makedirs(outdir_path, exist_ok=True)

# 道路グラフネットワーク取得
graphml_outfile = outdir_path / "road_network.graphml"
if not os.path.isfile(graphml_outfile):
    # 走行可能な道路グラフネットワークを取得
    G = ox.graph_from_place(query, network_type="drive")
    # 取得データを再利用目的でGraphml形式にて保存
    ox.save_graphml(G, filepath=graphml_outfile)
else:
    # 前回取得の道路グラフネットワークを再利用
    G = ox.load_graphml(graphml_outfile)

# 道路グラフネットワーク可視化
fmap = ox.plot_graph_folium(G)
folium_outfile = outdir_path / "road_network.html"
fmap.save(outfile=str(folium_outfile))

png_outfile = outdir_path / "road_network.png"
opts = {"node_size": 5, "bgcolor": "white", "node_color": "blue", "edge_color": "blue"}
ox.plot_graph(G, show=False, save=True, filepath=png_outfile, **opts)

# 道路グラフネットワークの各ノード・エッジ取得・CSV出力
nodes, edges = ox.graph_to_gdfs(G)
nodes_csv_outfile = outdir_path / "road_network_nodes.csv"
nodes.to_csv(nodes_csv_outfile)
edges_csv_outfile = outdir_path / "road_network_edges.csv"
edges.to_csv(edges_csv_outfile)

# 最短経路探索
start_point = (34.9575433,135.1765975)
start_node = ox.get_nearest_node(G, start_point)
end_point = (34.8867174,135.2049631)
end_node = ox.get_nearest_node(G, end_point)

shortest_path = ox.shortest_path(G, start_node, end_node)

# 最短経路探索結果の可視化
new_fmap = ox.plot_route_folium(G, shortest_path, route_map=fmap, color="red")
folium.Marker(location=start_point, tooltip="start").add_to(new_fmap)
folium.Marker(location=end_point, tooltip="end").add_to(new_fmap)

for point in parking_database:
    folium.Marker(
        location=[point[1],point[2]],
        popup='shop  '+str(point[0]),
        icon=folium.Icon(color='red')
    ).add_to(new_fmap)

folium_path_outfile = outdir_path / "shortest_path_road_network.html"
new_fmap.save(outfile=str(folium_path_outfile))

path_png_outfile = outdir_path / "shortest_path_road_network.png"
ox.plot_graph_route(
    G, shortest_path, show=False, save=True, filepath=path_png_outfile, **opts
)
