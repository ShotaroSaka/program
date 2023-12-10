#!/usr/bin/env python3
import os
import sys
import osmnx as ox
import taxicab as tc
import numpy as np

import random 
random.seed(1)


class Place(object):
    def __init__(self, latitude, longitude, population):
        self._lat = latitude     # 緯度
        self._lon = longitude    # 経度
        self._pop = population   # 人気度の重み

    def set_id(self, id):
        self._id = id           
   

        
class EV(object):
    def __init__(self, id):
        self._id = id
        self.candidate_EVA = None  # EV_i の行き先候補となる EVA

        # 出発地の決定
        self.select_departure()

        # 目的地数および目的地候補の決定
        destination_num = self.determine_num_of_destinations()
        self.select_destination(destination_num)

        # 世帯数を決定し，世帯数をもとに消費電力および発電量を決定
        # 消費電力および発電量から S or B を決定
        household_size = self.determine_num_of_households()
        self.set_consumption(household_size) 
        self.set_power_generation()
        self.set_kind()

        
    def select_departure(self) -> object:
        '''出発地点リストの中から人気度の重みをもとにランダムに一つ出発地点を選ぶ関数
           研究では，全て同じ人気度となっている'''
        dep_pop = [dep._pop for dep in sim._dep_list]
        selected_dep = random.choices(sim._dep_list[:],
                                      k = 1,
                                      weights = dep_pop)

        self.departure_point = selected_dep[0]

        
    def determine_num_of_destinations(self):
        '''目的地の数を決定する関数
           50％の確率で全ての目的地を選択'''
        if random.random() >= 0.5: return 1
        else:                      return len(sim._des_list)

        
    def select_destination(self, des_num) -> object:
        '''目的地リストから des_num 個目的地候補を選ぶ関数'''
        des_pop_list = [des._pop for des in sim._des_list]   
        # 目的地リストの中から des_num 個目的地候補を選択しリストで格納
        selected_des = self.weighted_choice_no_duplicates(sim._des_list[:],
                                                          k = des_num,
                                                          weights = des_pop_list)

        self.destinations_list = selected_des
  

    def weighted_choice_no_duplicates(self, place_list, k, weights):
        '''目的地リストの中から重みあり，重複なしで目的地を k 個選択
           選択した目的地を配列 select_place に格納'''
        select_place = []
        for i in range(k):
            tmp = random.choices(range(len(place_list)), weights)[0]
            select_place.append(place_list.pop(tmp))
            weights.pop(tmp)

        return select_place

    
    def set_candidates_EVA(self, select_EVA):
        self.candidate_EVA = select_EVA


    def determine_num_of_households(self):
        probabilities = [0.289, 0.222, 0.192, 0.080]
        household_sizes = [2, 3, 4, 5]

        # 確率に基づいて世帯数を選択
        household_size = random.choices(household_sizes, probabilities)[0]

        return household_size

    
    def set_consumption(self, household_size):
        # 世帯数に応じた消費電力量の平均と分散
        means = [10.5, 12.2, 13.1, 16.6]
        variances = [1.0, 1.0, 1.0, 1.0]
        
        mean = means[household_size - 2]
        variance = variances[household_size - 2]

        # 正規分布からランダムな消費電力を設定
        self.consumption_E_kWh = np.random.normal(mean, np.sqrt(variance))
     

    def set_power_generation(self):
        # 発電量を設定
        mean = 12.1
        variance = 1.0

        self.generated_E_kWh = np.random.normal(mean, np.sqrt(variance))
    

    def set_kind(self, trade_p):
        # 発電量 - 消費量の値をもとに S or B を決定
        self.request_E_kWh = self.generated_E_kWh - self.consumption_E_kWh
        
        if self.request_E_kWh > 0:  self.kind = 'S'
        else:                       self.kind = 'B'
        
        
    def print_information(self):
        '''出発地と目的地候補をプリント'''
        print("出発地点: {0}".format(self.departure_point._id))
        print("目的地候補の数: {0}".format(self.destination_num))
        print("目的地候補: ", end = "")
        for des in self.destinations_list:
            print(des._id, end = " ")
        print()            
        
               
    def print_select_EVA_distance_file(self) -> None:
           # EVAの行き先候補をプリント(実験用)
           # EVA_id と目的地からの距離
           # ex)  SorB request_E_kWh dep_id id_1 id_2 id_3 dis_1 dis_2 dis_3
        print(str(self.kind) + " " , end = "")
        print(str(abs(self.request_E_kWh)) + " " , end = "")
        print(str(self.departure_point._id) + " " , end = "")
        for EVA_id in self.candidate_EVA.keys():
            print(str(EVA_id) + " " , end = "")
        for distance_m in self.candidate_EVA.values():
            print(str(distance_m) + " " , end = "")
        print()



class Simulate(object):
    def __init__(self):
        self._dep_list = []
        self._des_list = []
        self._EVA_list = []

        self.G = None                  # グラフネットワーク
        self.filer_distance_m = None   # 候補となる EVA を選択する際の基準となる距離
        
        self.distance_table = []       # 目的地 h とそれぞれの EVA の距離が格納されている（データベース）
        self.EVA_list = None           # EV i の候補と成る EVA の辞書（EVA_id : distance）
        
       
    def read_text_file(self, file, kind):
        '''ファイルの読み込み
        lat = 緯度，lon = 経度，pop = 人気度'''
        for line in open(file, 'r'):
            lat, lon, pop = map(float, line.split())
            place = Place(latitude = lat, longitude = lon, population = pop)

            if kind == "destination":   self.add_des(place)
            elif kind == "departure":   self.add_dep(place)
            elif kind == "EVA":         self.add_EVA(place)

    
    def add_dep(self, place) -> None:
        '''目的地のリストを作成'''
        self._dep_list.append(place)

    def add_des(self, place) -> None:
        '''出発地のリストを作成'''
        self._des_list.append(place)
    
    def add_EVA(self, place) -> None:
        '''EVA のリストを作成'''
        self._EVA_list.append(place)

              
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

    
    def assign_id(self) -> None:
        '''全ての場所に id を割り当てる'''
        [dep.set_id(i) for i, dep in enumerate(self._dep_list)]
        [des.set_id(i) for i, des in enumerate(self._des_list)]
        [EVA.set_id(i) for i, EVA in enumerate(self._EVA_list)]
   
                
    def measure_distance_des_to_EVA(self) -> None:
        '''全ての EVA と目的地の距離を先に格納
           EVA_dis_list は距離が格納されている二次配列'''
        for des in self._des_list:

            des_tmp = []
            for EVA in self._EVA_list:            
                des_place = (des._lat, des._lon)
                EVA_place = (EVA._lat, EVA._lon)
                
                # 二地点の緯度経度を入力すると，道のりの距離が出力される
                distance = tc.distance.shortest_path(self.G, des_place, EVA_place)
                # distance[0] には距離が格納されている
                des_tmp.append(round(distance[0]))

            self.distance_table.append(des_tmp)


    def set_distance_filter(self, filter_distance_m):
        self.filter_distance_m = filter_distance_m

            
    def select_EVA_from_destinations(self, destinations_list) -> None:
        '''目的地オブジェクトのリストを入力
           EVA のリストを出力'''
        # 一番近くの EVA の距離を新しい距離とする
        EVA_dis_list = self.calc_min_EVA_list(destinations_list)

        select_EVA_list = {}
        for EVA_id, EVA_dis in enumerate(EVA_dis_list):
            # 基準値以内の EVA を抽出(目的地周辺)
            if EVA_dis < self.filter_distance_m:
                select_EVA_list[EVA_id] = EVA_dis

        return select_EVA_list 
                
        
    def calc_min_EVA_list(self, destinations_list) -> list:
        '''目的地候補のリストを取得し，一番近い EVA の距離を格納する
           同じ要素同士を比較し，一番小さい値を min_distance_to_EVA に格納
           一次配列を出力'''
        min_distance_to_EVA = []
        for i in range(len(self._EVA_list)):
             distances = [self.distance_table[des._id][i] for des in destinations_list]
             min_dis = min(distances)
             min_distance_to_EVA.append(min_dis)

        return min_distance_to_EVA                    

    
    def simulation(self, n):
        for i in range(n):
            ev = EV(id = i)
            #ev.print_information()

            # 目的地候補から候補となる EVA を選択
            select_EVA_list = self.select_EVA_from_destinations(ev.destinations_list)
            ev.set_candidates_EVA(select_EVA_list)

            #ev.print_select_EVA_distance()
            ev.print_select_EVA_distance_file()


            
            
if __name__ == "__main__":
    sim = Simulate()

    num = sys.argv[1]
    filter_distance_m = int(sys.argv[2])
    
    # u  : ウッディータウンの意味
    # uf : ウッディータウン and フラワータウンの意味
    sim.read_text_file(file = "geographic_model/Sanda_departure_u.txt",     kind = "departure")
    sim.read_text_file(file = "geographic_model/Sanda_destination_u.txt",   kind = "destination")
    sim.read_text_file(file = "geographic_model/Sanda_EVA"+ num +"_u.txt",  kind = "EVA")

    
    # place のグラフネットワークを作成
    # 目的地から EVA までの距離をデータベースとして先に取得
    simulation_place = "Sanda,Hyogo,Japan"
    sim.create_graph(query = simulation_place)
    sim.assign_id()
    sim.measure_distance_des_to_EVA()

    
    # 目的地候補となる距離を設定
    sim.set_distance_filter(filter_distance_m)
    
    # 試行回数 (何台の EV を生成するか)
    n_trials = 1000
    sim.simulation(n_trials)
