import os
import sys
import osmnx as ox
import networkx as nx
import random
import taxicab as tc
random.seed(1)

         
class Place(object):
    def __init__(self, latitude, longitude, population):
        self._lat = latitude     # 緯度
        self._lon = longitude    # 経度
        self._pop = population   # 人口(重み計算の材料)

        self._num = None

    
    def set_id(self, id) -> None:
        self._place_id = id      # 場所のidを関数で取得
       

        
class Simulate(object):
    def __init__(self):
        self._des_list = []
        self._EVA_list = []
        self._dep_list = []

        self.G = None
       
        
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
            self.G = ox.graph_from_place(query, network_type = "drive")
            # 取得データを再利用目的でGraphml形式にて保存
            ox.save_graphml(self.G, filepath = graphml_outfile)
        else:
            # 前回取得の道路グラフネットワークを再利用
            self.G = ox.load_graphml(graphml_outfile)

            
    def all_get_id(self):  # 全てのidをGに格納しておく
        for EVA in self._EVA_list:
            point = (EVA._lat, EVA._lon)
            place_id = ox.get_nearest_node(self.G, point)
            EVA.set_id(place_id)
            
        for dep in self._dep_list:
            point = (dep._lat, dep._lon)
            place_id = ox.get_nearest_node(self.G, point)
            dep.set_id(place_id)

        for des in self._des_list:
            point = (des._lat, dep._lon)
            place_id = ox.get_nearest_node(self.G, point)
            des.set_id(place_id)


    def all_get_num(self):
        for i, EVA in enumerate(self._EVA_list):
            EVA._num = i
            
        for i, des in enumerate(self._des_list):
            des._num = i
      
        for i, dep in enumerate(self._dep_list):
            dep._num = i

         
    def random_dep_choice(self):  # 出発地点リストから一つの出発地点を選ぶ
        dep_pop = [dep._pop for dep in self._dep_list]        
        dep_choice = random.choices(self._dep_list, k = 1, weights = dep_pop)

        return dep_choice[0]

    
    def random_des_choice(self):  # 目的地リストから一つの目的地を選ぶ 
        des_pop = [des._pop for des in self._des_list]  
        des_choice = random.choices(self._des_list, k = 1, weights = des_pop)

        return des_choice[0]

            
    def get_shortest_path(self, start, end):  # 最短パスを求めている
        path = ox.shortest_path(self.G, start._place_id, end._place_id)  

        return path


    def pickup_EVA(self, path, end):          # 経路から範囲内にあるEVAを抽出する 
        EVA_id_list = []
        self.EVA_dis_list = {}
        
        for load in path:                     # 経路から100ｍ以内のEVAをpickup
            for EVA in self._EVA_list:
                dis = nx.shortest_path_length(self.G, EVA._place_id, load, weight = 'length')
                if dis <= 1000:
                    EVA_id_list.append(EVA._num)
                    
        for EVA in self._EVA_list:            # 目的地近くのEVAを抽出
            place = (EVA._lat, EVA._lon)
            goal = (end._lat, end._lon)
            dis = tc.distance.shortest_path(self.G, place, goal)
            self.EVA_dis_list[EVA._num] = round(dis[0])
            if dis[0] <= 1000:
                EVA_id_list.append(EVA._num)     

        self.EVA_list = list(set(EVA_id_list))


    def print_start_end(self, start, end):
        print("出発地点: {0} 目的地: {1}"
              .format(start._num, end._num))

        
    def print_EVA(self):
        dis_list = []
        for i in self.EVA_list:
            dis_list.append(self.EVA_dis_list.pop(i))

        for id, dis in zip(self.EVA_list, dis_list):
            print("id: {0} dis: {1} ".format(id, dis))
        print()


        
def read_csv(file):  # ファイルの読み込み
    data = []
    for line in open(file, 'r'):
        lat, lon, pop = map(float, line.split(","))
        data.append([lat, lon, pop])
     
    return data


def make_class(data, name, sim):
    for d in data:
        place = Place(latitude = d[0], longitude = d[1], population = d[2])  #格納するデータ(緯度，経度，人口)
        if name == "destination":   sim.add_des(place)
        elif name == "departure":   sim.add_dep(place)
        elif name == "EVA":         sim.add_EVA(place)

    

            
def main():
    place = "Sanda,Hyogo,Japan"
    shop_list = read_csv("Sanda_shop_list.csv")
    EVA_list = read_csv("Sanda_parking_list.csv")
    house_list = read_csv("Sanda_population_list.csv")

    sim = Simulate()
    make_class(shop_list, "destination", sim)
    make_class(EVA_list, "EVA", sim)
    make_class(house_list, "departure", sim)

    sim.create_graph(place)
    sim.all_get_id()
    sim.all_get_num()


    n = int(sys.argv[1])  # 試行回数
    
    for i in range(n):
        start_point = sim.random_dep_choice()  # スタート地点の決定
        end_point = sim.random_des_choice()    # 目的地の決定
        
        
        path = sim.get_shortest_path(start_point, end_point)  # スタート地点と目的地を繋ぐパスの取得
        sim.pickup_EVA(path, end_point)                       # パスからA(i)を決定

        sim.print_start_end(start_point, end_point)
        sim.print_EVA()
        
      
if __name__ == "__main__":
    main()
