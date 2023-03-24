import os
import sys
import osmnx as ox
import math
import taxicab as tc

import random 
random.seed(1)


class Place(object):
    def __init__(self, latitude, longitude, population):
        self._lat = latitude     # 緯度
        self._lon = longitude    # 経度
        self._pop = population   # 人気度の重み

        self._id = None           
   

        
class Simulate(object):
    def __init__(self):
        self._dep_list = []
        self._des_list = []
        self._EVA_list = []

        self.EVA_dis_list = []   # 目的地と EVA の距離が格納されている
        self.EVA_list = []       # 選ばれた EVA
        
        self.G = None            # グラフネットワーク

    
    def add_dep(self, Place) -> None:
        '''目的地のリストを作成'''
        self._dep_list.append(Place)

    def add_des(self, Place) -> None:
        '''出発地のリストを作成'''
        self._des_list.append(Place)
    
    def add_EVA(self, Place) -> None:
        '''EVA のリストを作成'''
        self._EVA_list.append(Place)

              
    def create_graph(self, query) -> None:
        '''道路グラフネットワーク取得
           G に情報を格納'''
        graphml_outfile = "road_network.graphml"        
        if not os.path.isfile(graphml_outfile):
            # 走行可能な道路グラフネットワークを取得
            self.G = ox.graph_from_place(query, network_type = "drive")
            # 取得データを再利用目的で Graphml 形式にて保存
            ox.save_graphml(self.G, filepath = graphml_outfile)
        else:
            # 前回取得の道路グラフネットワークを再利用
            self.G = ox.load_graphml(graphml_outfile)

    
    def get_all_id(self) -> None:
        '''全ての場所 id を G に格納
           場所の id と id をそれぞれの場所に格納'''
        for i, dep in enumerate(self._dep_list):
            dep._id = i
    
        for i, des in enumerate(self._des_list):
            des._id = i

        for i, EVA in enumerate(self._EVA_list):
            EVA._id = i

                
    def get_distance_des_to_EVA(self) -> None:
        '''全ての EVA と目的地の距離を先に格納
           EVA_dis_list は距離が格納されている二次配列'''
        for des in self._des_list:

            # 一時的に使う配列
            tmp = []

            # 全 EVA までの距離を測定
            for EVA in self._EVA_list:            
                EVA_place = (EVA._lat, EVA._lon)
                des_place = (des._lat, des._lon)

                # 二地点の緯度経度を入力すると，道のりの距離が出力される
                dis = tc.distance.shortest_path(self.G, des_place, EVA_place)

                # dis[0] には距離が格納されている
                tmp.append(round(dis[0]))

            self.EVA_dis_list.append(tmp)
        
    
    def choice_random_dep(self) -> object:
        '''出発地点リストの中から重みをもとにランダムに一つ出発地点を選ぶ'''
        dep_pop = [dep._pop for dep in self._dep_list]
        dep_choice = random.choices(self._dep_list, k = 1, weights = dep_pop)

        return dep_choice[0]

    
    def choice_random_des(self, des_num) -> object:
        '''目的地リストから des_num 個目的地候補を選ぶ
           多項ロジットモデルで２つの指標（人気度，距離）を用いて決定'''
        des_pop_list = [des._pop for des in self._des_list]   
        # 目的地リストの中から des_num 個目的地候補を選択しリストで格納
        des_choice = self.random_choices(self._des_list[:], des_num, des_pop_list)
        
        return des_choice


    def random_choices(self, plist, n, weights):
        '''目的地リストの中から重みあり，重複なしで目的地を n 個選択
           選択した目的地を配列 ret に格納'''
        ret = []
        for i in range(n):
            idx = random.choices(range(len(plist)), weights)[0]
            ret.append(plist.pop(idx))
            weights.pop(idx)

        return ret 
            
    
    def calc_pro(self, v_list) -> list:
        '''ガンベル分布に従うように効用からそれぞれの選択確率に変換
           pr はそれぞれの選択確率が格納された配列'''
        sum = 0
        for i in v_list:
            sum += math.exp(self._lamda*i)
        pr = [math.exp(self._lamda*j) / sum for j in v_list]

        return pr
    
        
    def pickup_EVA(self, des_place_list) -> None:
        '''目的地オブジェクトのリストを入力
           EVA のリストを出力'''
        
        # 一番近くの EVA の距離を新しい距離とする
        self.new_EVA_dis_list = self.calc_new_EVA_list(des_place_list)

        # 行き先候補の EVAid を一時的に格納する配列
        EVA_id_list = []
        for dis, EVA in zip(self.new_EVA_dis_list, self._EVA_list):
            # 500m 以内の EVA を抽出(目的地周辺)
            if dis <= 500:
                EVA_id_list.append(EVA._id)

        self.EVA_list = list(set(EVA_id_list))

                
        
    def calc_new_EVA_list(self, des_list):
        '''目的地候補のリストを入力し，一番近い EVA の距離を格納する
           同じ要素同士を比較し，一番小さい値を new_EVA_dis_list に格納
           一次配列を出力'''

        self.new_EVA_dis_list = []
        # 全 EVA 回比較を行う
        for j in range(len(self._EVA_list)):
            # 目的地リストで選ばれたものだけ比較
            min_dis = 100000
            for des in des_list:
                if min_dis > self.EVA_dis_list[des._id][j]:
                    min_dis = self.EVA_dis_list[des._id][j]
                    
            # 一番距離の短い EVA を格納
            self.new_EVA_dis_list.append(min_dis)

        return self.new_EVA_dis_list


    def print_des_factor(self, des_id, des_pop, dis, V):
        '''目的地の効用をプリント(確認用)'''
        print("目的地id: {0} 目的地の人気度: {1} 目的地までの距離: {2} 目的地の効用: {3}"
              .format(des_id, des_pop, dis, V))
        
                                
    def print_start_end_place(self, num, start) -> None:
        '''出発地と目的地候補をプリント'''
        print("出発地点: {0}".format(start._id))
        print("目的地候補の数: {0}". format(num))

              
    def print_pickup_EVA_distance(self, end_list) -> None:
        '''EVAの行き先候補をプリント(確認用)
           EVA_id と目的地からの距離
           ex)  id: x  dis: y'''
        print("目的地候補: ", end = "")
        for end in end_list:
            print(end._id, end = " ")
        print()
        
        for EVA_id in self.EVA_list:
            print("id: {0} dis: {1}".format(EVA_id, self.new_EVA_dis_list[EVA_id]))
        print()
        print()
        
       
    def print_file_pickup_EVA_distance(self) -> None:
        '''EVAの行き先候補をプリント(実験用)
           EVA_id と目的地からの距離
           ex)  id_1 id_2 id_3 dis_1 dis_2 dis_3 '''
        for EVA_id in self.EVA_list:
            print(str(EVA_id) + " " , end = "")
        for EVA_id in self.EVA_list:
            print(str(self.new_EVA_dis_list[EVA_id]) + " " , end = "")
        print()    
            

        
        


def read_csv(file):
    '''ファイルの読み込み
       lat = 緯度，lon = 軽度，pop = 人気度'''
    data = []
    for line in open(file, 'r'):
        lat, lon, pop = map(float, line.split())
        data.append([lat, lon, pop])
     
    return data


def make_class(data, name, sim):
    '''クラスを作成し，それぞれに追加'''
    for d in data:
        # 格納するデータ(緯度，経度，人口)
        place = Place(latitude = d[0], longitude = d[1], population = d[2])  
        if name == "destination":   sim.add_des(place)
        elif name == "departure":   sim.add_dep(place)
        elif name == "EVA":         sim.add_EVA(place)

    

            
def main():
    place = "Sanda,Hyogo,Japan"
    house_list = read_csv("Sanda_home_uf.txt")
    shop_list = read_csv("Sanda_shop_uf.txt")
    EVA_list = read_csv("Sanda_parking_uf.txt")

    sim = Simulate()
    make_class(house_list, "departure", sim)
    make_class(shop_list, "destination", sim)
    make_class(EVA_list, "EVA", sim)
    
    # place のグラフネットワークを作成
    sim.create_graph(query = place)
    sim.get_all_id()
    sim.get_distance_des_to_EVA()

    l = [1, 4]   
    
    # 試行回数
    n = int(sys.argv[1])  
    for i in range(n):
        # スタート地点，目的地の数を決定
        start_point = sim.choice_random_dep()                          
        dis_num = random.choice(l)
        sim.print_start_end_place(dis_num, start_point)

        # 目的地の候補を決定
        end_point_list = sim.choice_random_des(dis_num)        
       
        # 目的地候補から EVA を抽出
        sim.pickup_EVA(end_point_list)

        sim.print_pickup_EVA_distance(end_point_list)
        #sim.print_file_pickup_EVA_distance()
      
if __name__ == "__main__":
    main()

