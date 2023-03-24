from datetime import datetime

import dill
import overpy


import os
from pathlib import Path

import folium
import osmnx as ox

import pandas as pd

def input_node_info():
    key = input('Input node key:')
    tag = input('Input tag of key:')
    return key, tag
     
def read_csv(file):
    filename = file   #読み込むファイル
    data = pd.read_csv(filename, header=None)   #データの読み込み

    return data


def main():
    #key, tag = input_node_info()
    key="amenity"
    tag="parking"
    result=fetch_result(key, tag)

    print(result.nodes)
    
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
    start_point = (34.883, 135.22820)
    start_node = ox.get_nearest_node(G, start_point)
    end_point = (34.8825125, 135.2299860)
    end_node = ox.get_nearest_node(G, end_point)

    
    print(start_node)
    print(end_node)
    shortest_path = ox.shortest_path(G, start_node, end_node)
    print(shortest_path)
    # 最短経路探索結果の可視化
    new_fmap = ox.plot_route_folium(G, shortest_path, route_map=fmap, color="red")
    folium.Marker(location=start_point, tooltip="start").add_to(new_fmap)
    folium.Marker(location=end_point, tooltip="end").add_to(new_fmap)

    folium.Circle(
        location = end_point
        , radius=1000 
        , color="#f9f94e"
        , fill=True
        , fill_color="#cef58e"
    ).add_to(new_fmap)

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
if __name__ == "__main__":
    main()
