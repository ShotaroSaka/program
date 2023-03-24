import os
import sys
import folium
import osmnx as ox
import taxicab as tc

class Place(object):
    def __init__(self, latitude, longitude):
        self._lat = latitude  # 緯度
        self._lon = longitude  # 経度


class Simulate(object):
    def __init__(self):
        self._des_list = []
        self._EVA_list = []
        self._dep_list = []

        self.G = None
        self.new_fmap = None


    def read_csv(self, file):  # ファイルの読み込み
        data = []
        for line in open(file, 'r'):
            lat, lon, pop = map(float, line.split())
            data.append([lat, lon, pop])

        return data

    
    def add_des(self, Place):  # 出発地点のリスト
        self._des_list.append(Place)

        
    def add_EVA(self, Place):  # EVA地点のリスト
        self._EVA_list.append(Place)

        
    def add_dep(self, Place):  # 目的地のリスト
        self._dep_list.append(Place)
            
            
    def create_graph(self, query):
        # 道路グラフネットワーク取得
        graphml_outfile = "road_network.graphml"
        if not os.path.isfile(graphml_outfile):
            # 走行可能な道路グラフネットワークを取得
            self.G = ox.graph_from_place(query, network_type="drive")
            # 取得データを再利用目的でGraphml形式にて保存
            ox.save_graphml(self.G, filepath=graphml_outfile)
        else:
            # 前回取得の道路グラフネットワークを再利用
            self.G = ox.load_graphml(graphml_outfile)

        
    def shortest_path(self, start, end):
        start_point = (self._des_list[start]._lat, self._des_list[start]._lon)
        start_node = ox.get_nearest_node(self.G, start_point)

        end_point = (self._EVA_list[end]._lat, self._EVA_list[end]._lon)
        end_node = ox.get_nearest_node(self.G, end_point)

        self.path = ox.shortest_path(self.G, start_node, end_node)
        print(self.path)

        
    def create_file(self):
        # 道路グラフネットワーク可視化
        fmap = ox.plot_graph_folium(self.G)
        # 最短経路探索結果の可視化
        self.new_fmap = ox.plot_route_folium(self.G, self.path, route_map=fmap, color="red")
        

    def marker_point_dep(self):
        i = 0
        for place in self._dep_list:
            folium.Marker(
                location = [place._lat, place._lon],
                popup = "home" + str(i),
                icon = folium.Icon(color = "red")
            ).add_to(self.new_fmap)
            i += 1

            
    def marker_point_des(self):
        i = 0
        for place in self._des_list:
            folium.Marker(
                location = [place._lat, place._lon],
                popup = "shop" + str(i),
                icon = folium.Icon(color = "black")
            ).add_to(self.new_fmap)
            i += 1

            
    def  marker_point_EVA(self):
        i = 0
        for place in self._EVA_list:
            folium.Marker(
                location = [place._lat, place._lon],
                popup = "EVA" + str(i),
                icon = folium.Icon(color = "green")
            ).add_to(self.new_fmap)
            i += 1

            
    def save_file(self):
        folium_path_outfile = "all_place.html"
        self.new_fmap.save(outfile=str(folium_path_outfile))

            
            
def make_class(data, name, sim):
    if name == "destination":
        for d in data:
            des = Place(latitude = d[0], longitude = d[1]) 
            sim.add_des(des)

    elif name == "departure":
        for d in data:
            dep = Place(latitude = d[0], longitude = d[1])
            sim.add_dep(dep)
            
    elif name == "EVA":
        for d in data:
            EVA = Place(latitude = d[0], longitude = d[1])
            sim.add_EVA(EVA)





def main():
    start_id = int(sys.argv[1])
    end_id = int(sys.argv[2])
    sim = Simulate()
    
    place = "Sanda,Hyogo,Japan"
    shop_list = sim.read_csv("Sanda_shop_uf.txt")
    EVA_list = sim.read_csv("Sanda_parking_uf.txt")
    house_list = sim.read_csv("Sanda_home_uf.txt")
   
    make_class(shop_list, "destination", sim)
    make_class(house_list, "departure", sim)
    make_class(EVA_list, "EVA", sim)

    sim.create_graph(place)
    sim.shortest_path(start_id, end_id)
    sim.create_file()

    sim.marker_point_des()
    sim.marker_point_dep()
    sim.marker_point_EVA()
    
    sim.save_file()
    

if __name__ == "__main__":
    main()
