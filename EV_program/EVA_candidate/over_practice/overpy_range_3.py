from datetime import datetime

import dill
import overpy


import os
from pathlib import Path

import folium
import osmnx as ox

import time
import networkx as nx

def input_node_info():
    key = input('Input node key:')
    tag = input('Input tag of key:')
    return key, tag

#node(around:1000:34.8825125, 135.2299860)["{key}"="{tag}"];\n'

def fetch_result(key, tag):
    api = overpy.Overpass()
    query = (
        'area["name"~"三田市"];\n'
        'node(area)["{key}"="{tag}"];\n'
        'out;'
    ).format(key=key, tag=tag)
    print('Fetch query...')
    result = api.query(query)
    
    print("success")

    
    return result


    
def create_graph(key,tag,query,result):
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
    
    start_point = (34.90920, 135.19544)
    start_node = ox.get_nearest_node(G, start_point)
    end_point = (34.8825125, 135.2299860)
    end_node = ox.get_nearest_node(G, end_point)

    print(start_node)
    print(end_node)
    shortest_path = ox.shortest_path(G, start_node, end_node)
    
   
    
    # 最短経路探索結果の可視化
    new_fmap = ox.plot_route_folium(G, shortest_path, route_map=fmap, color="red")
    folium.Marker(location=start_point, tooltip="start").add_to(new_fmap)
    folium.Marker(location=end_point,radius=1000, tooltip="end").add_to(new_fmap)

    for load in shortest_path:
        for node in result.nodes:
            print(round(nx.shortest_path_length(G, load, node.id, weight='length'))

                  
    for node in result.nodes:
        folium.Marker(
            location=[node.lat,node.lon],
            popup='convenience',
            icon=folium.Icon(color='red')
        ).add_to(new_fmap)

                  
    folium_path_outfile = outdir_path / "shortest_path_road_network.html"
    new_fmap.save(outfile=str(folium_path_outfile))

    path_png_outfile = outdir_path / "shortest_path_road_network.png"
    ox.plot_graph_route(
        G, shortest_path, show=False, save=True, filepath=path_png_outfile, **opts
    )
    



def main():
    key, tag = input_node_info()
    result=fetch_result(key, tag)

    query = "Sanda,Hyogo,Japan"
    create_graph(key,tag,query,result)
    
if __name__ == "__main__":
    main()
