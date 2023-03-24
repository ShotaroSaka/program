import os
from pathlib import Path
import folium
import osmnx as ox
import networkx as nx
import pandas as pd
import random
import csv

def read_csv(file):
    filename = file   #読み込むファイル
    data = pd.read_csv(filename, header=None)   #データの読み込み

    return data


def write_csv(file, data_list):
    with open(file, "w", newline="") as f:
        writer = csv.writer(f)
        for data in data_list:
            writer.writerow(data)
    f.close()

    
def marker_point(lon,lat,name,G):  #抽出下地点にマークを付ける
    folium.Marker(
        location = [lon, lat],
        popup = name,
        icon = folium.Icon(color = 'red')
    ).add_to(G)


def shortest_path(start, goal, G):  #スタート地点とゴール地点を入力，最短パス（ノードの配列を出力
    start_node = ox.get_nearest_node(G, start)
    end_node = ox.get_nearest_node(G, goal)
    path = ox.shortest_path(G, start_node, end_node)

    return path


def pickup_EVA(route, EVA_id, G):
    EVA_id_list = []
    if route == None:
        return list(set(EVA_id_list))
    
    for load in route[:len(route)-1:5]:  #経路途中にあるEVAを抽出（全部は多いから５つ飛ばしで）
        for i in range(len(EVA_id)):
            try:
                dis = round(nx.shortest_path_length(G, EVA_id[i][0], load, weight='length'))
            except:                      #経路が見つからない場合
                continue
            if dis <= 100:               #経路から100ｍ以内のEVAをpickup
                EVA_id_list.append( [EVA_id[i][0],EVA_id[i][1],EVA_id[i][2]])
                    
                
    for i in range(len(EVA_id)):                    #目的地近くのEVAを抽出
        dis = round(nx.shortest_path_length(G, EVA_id[i][0], route[-1], weight='length'))
        if dis <= 800:                   #範囲が500m以内のEVAをpickup
            EVA_id_list.append( [EVA_id[i][0],EVA_id[i][1],EVA_id[i][2]] )
            
    
    return EVA_id_list



def create_graph(query, house_list, EVA_list, shop_list, kkk):   
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


    
    EVA_id_list = []  #全てのEVAのidを格納する
    for i in range(len(EVA_list)):
        point = (EVA_list[1][i],EVA_list[2][i])
        EVA_id_list.append([ox.get_nearest_node(G, point),EVA_list[1][i],EVA_list[2][i]])

        
    select_EVA = []  #EViのA(i)が格納される

    
    start_point = (house_list[1][kkk], house_list[2][kkk])  #出発地点の緯度経度
    end_point = (shop_list[1][kkk], shop_list[2][kkk])  #目的地の緯度経度
    path = shortest_path(start_point, end_point, G)  #最短経路を求める関数
    select_EVA.append(pickup_EVA(path, EVA_id_list, G))  #経路と全てのEVAを引数にして，A(i)を求める

    print(start_point, end_point)
    print(select_EVA)
   
    
    new_fmap = ox.plot_route_folium(G, path, route_map=fmap, color="red")
    folium.Marker(location=start_point, tooltip="start").add_to(new_fmap)
    folium.Marker(location=end_point, tooltip="end").add_to(new_fmap)

    print(select_EVA)
    for i in range(len(select_EVA[0])):    
        print(select_EVA[0][i][1], select_EVA[0][i][2])
        marker_point(select_EVA[0][i][1], select_EVA[0][i][2], "EVA", new_fmap)


                                
    folium_path_outfile = outdir_path / "shortest_path_road_network.html"
    new_fmap.save(outfile=str(folium_path_outfile))

    path_png_outfile = outdir_path / "shortest_path_road_network.png"
    ox.plot_graph_route(
        G, path, show=False, save=True, filepath=path_png_outfile, **opts
    )
         

def main():

    i = 2
    place = "Sanda,Hyogo,Japan"
    shop_list = read_csv("Sanda_shop_list.csv")
    EVA_list = read_csv("Sanda_parking_list.csv")
    house_list = read_csv("Sanda_departure_list.csv")
        
    select_EVA = create_graph(place, house_list, EVA_list, shop_list, i)
    

    
if __name__ == "__main__":
    main()
