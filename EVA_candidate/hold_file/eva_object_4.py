import sys
import math
import numpy as np
from scipy.integrate import odeint
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

import random
random.seed(2)

import os
import osmnx as ox
import networkx as nx
import csv



stT = 0             # 開始時間
endT = 6            # 終了時間

init_x = 1.0        # initial rates of EVs
init_p = 0.0        # initial price→pena

alpha = 2           ## parameter setting for ev # parameter of the utility function for buyers 
beta = 2




class Destination(object):
    def set_place(self, latitude, longitude, population):
        self._lat = latitude  # 緯度
        self._lon = longitude  # 経度
        self._pop = population  # 人口(重み計算の材料)

    
    def set_id(self, id):
        self._place_id = id  # 場所のidを関数で取得 




class EV(object) :
    def __init__(self, id, kind) :
        self._id = id         # identification number of the EV group
        self._kind = kind     # kind of EVs (kind = 'S' or kind = 'B') in the group
        self._kappa_s = 1000  # 売電価格の計算式における係数
        self._kappa_b = 1000  # 買電価格の計算式における係数

        
    def set_time(self, arrT, depT, t_a) :
        self._arrT = arrT         # arrival time of EV
        self._depT = depT         # departure time of EV
        self._t_a = t_a           # 現在の時間をもたせる
    

    def set_place(self, latitude, longitude, population, sim):
        self._lat = latitude    # 緯度
        self._lon = longitude   # 経度
        self._pop = population  # 人口(重み計算の材料)
        self.set_id(sim)

        self._dis_list = []     # 各EVAの距離

        
    def set_calc_param(self, gamma, kappa_r, base_p, Es, Eb) :
        self._gamma = gamma         # parameter of the utility function
        self._kappa_r = kappa_r     # coefficient used in the derivs
        self._base_p = base_p       # base line of price

        self._Es = Es               
        self._Eb = Eb
        self._E_now = 0             # 今まで取引した電力量
        self._rate = None           # EViに流れている電力レート
        self._gamma_fact = 2        # 価格の計算式に用いられているガンマ

        self.set_price_param()

        
    def set_price_param(self):
        if self._kind == 'S' : 
            self._price = self._Es*self._base_p         # 一台しかいないときに値段（一番良い値段）
            self._price_pre = self._Es*self._base_p     # EVステーションの混雑具合で変動する価格
            self._price_rate = self._base_p             # 単位電力量あたりの価格
            
        elif self._kind == 'B' :
            self._price = self._Eb*self._base_p
            self._price_pre = self._Eb*self._base_p
            self._price_rate = self._base_p


    def set_id(self, sim):
        point = (self._lat, self._lon)
        id = ox.get_nearest_node(sim._G, point)        
        self._place_id = id
           
    
    def derivs_util(self, x) :
        return (x + 1)**(-self._gamma)   # differential equation of the utility function

    
    def derivs_x(self, x, p) :
        return self._kappa_r*(self.derivs_util(x) - p*x)  # differential equation of the rate

    
    def calc_price(self, rate, p, t1) :
        if self._kind == 'S' :    # for sellers
            self._price -= (self._kappa_s * rate**(self._gamma_fact)
                            * (p[0] - p[2]) * (t1 - self._t_a))    

            self._price_pre = (self._price - (self._kappa_s * rate**(self._gamma_fact)
                               * (p[0] - p[2]) * (self._depT - t1)))        

            self._price_rate = (rate*self._base_p - self._kappa_s
                                * rate**(self._gamma_fact)*(p[0] - p[2]))   # 価格決定式
            
        elif self._kind == 'B' :  # for buyers
            self._price += (self._kappa_b * rate**(self._gamma_fact)
                            * (p[1] + p[2]) * (t1 - self._t_a))

            self._price_pre = (self._price + (self._kappa_b * rate**(self._gamma_fact)
                               * (p[1] + p[2]) * (self._depT - t1))) 

            self._price_rate = (rate*self._base_p + self._kappa_b
                                *rate**(self._gamma_fact)*(p[1] + p[2]))   # 価格決定式

            
    def calc_E_now(self, rate, t1):  # 完了した電力量
        self._E_now += rate*(t1 - self._t_a)
    


    
class EVA(object) :
    def __init__(self, id) :
        self._id = id
        self._EV_list = {}

        
    def set_param(self, k1, k2, k3, limit_As, limit_Ar, rs, rb) :
        self._k1 = k1                  # EVAkでのペナルティ
        self._k2 = k2
        self._k3 = k3
        
        self._kappa_dis = 1            # 多項ロジットモデルでの重み（距離）
        self._kappa_price_s = 0.1      # 多項ロジットモデルでの重み（売り手の値段）
        self._kappa_price_b = -0.1     # 多項ロジットモデルでの重み（買い手の値段）

        self._limit_As = limit_As      # ケーブル容量
        self._limit_Ar = limit_Ar
        
        # self._dis = dis              # EVとEVA間の距離
        self._s_num = 1                # EViにいる売り手EVの数
        self._b_num = 1                # EViにいる買い手EVの数



    def set_place(self, latitude, longitude, population):
        self._lat = latitude       # 緯度
        self._lon = longitude      # 経度
        self._pop = population     # 人口(重み計算の材料)

    
    def set_id(self, id):
        self._place_id = id              # 場所のidを関数で取得

        
    def add_EV(self, EV):
        self._EV_list[EV._id] = EV
   
        
    def derivs_p1(self, As) :
        return self._k1*(As - self._limit_As)
    
    def derivs_p2(self, Ar) :
        return self._k2*(Ar - self._limit_Ar)

    def derivs_p3(self, As, Ar) :
        return self._k3*(Ar - As)

    
    def derivs_p(self, As, Ar, p1, p2, p3):
        dp1 = self.derivs_p1(As)
        dp2 = self.derivs_p2(Ar)
        dp3 = self.derivs_p3(As, Ar)

        return [dp1, dp2, dp3]

    
    def calc_depT(self, rate):    # 電力売買が完了する時間を計算
        for ev in self._EV_list.values():
            if ev._kind == "S":
                ev._depT = ev._t_a + (ev._Es - ev._E_now)/rate
                
            elif ev._kind == "B":
                ev._depT = ev._t_a + (ev._Eb - ev._E_now)/rate


    def set_init(self, init_x, init_p):
        self._init = [init_x]*len(self._EV_list) + [init_p]*3


    def get_conv(self, e_time):
        self._opt = minimize(self.norm_derivs, self._init)   # その時のレートとペナルティを計算
        EV_n = len(self._EV_list)
        x = {}

        p1 = self._opt.x[EV_n]
        p2 = self._opt.x[EV_n + 1]
        p3 = self._opt.x[EV_n + 2]

        i = 0
        for ev in self._EV_list.values():
            x[i] = self._opt.x[i]                   # レート of EV id
            ev._rate = x[i]

            ev.calc_price(x[i], (p1, p2, p3), e_time)   # 価格を更新する（etimeまでの合計価格）
            ev.calc_E_now(x[i], e_time)             # etimeまでの総充電量
            ev._t_a = e_time                        # 今の時間を保存する

            self.calc_depT(x[i])                    # レートとenowが更新されたので，depTを計算する

            i += 1

            
    def derivs(self, t, y):
        """
           calculate
        """ 
        ## calculate the both aggregate rates of sellers and buyers.
        As = Ar = 0.0
        i = 0
        for ev in self._EV_list.values():
            if ev._kind == 'S' :    As += y[i]
            elif ev._kind == 'B' :  Ar += y[i]
            else :                assert(False)

            i += 1

        ## get price
        p1 = y[i]
        p2 = y[i+1]
        p3 = y[i+2]

        ## calculate the derivs of stats
        dy = []
        i = 0
        for ev in self._EV_list.values() :
            x = y[i]
            if ev._kind == 'S' :    p = p1 - p3
            elif ev._kind == 'B' :  p = p2 + p3
            else :                assert(False)

            dy.append(ev.derivs_x(x, p))
            i += 1

        dy = dy + self.derivs_p(As, Ar, p1, p2, p3)

        return dy


    def norm_derivs(self, y) :
        """
        calculate the normalized norm of the derivs vector 
           ** This norm is used to obtain the convergenced value of state

        Args :
           y (list of float) : states
        Returns :
           float : normalized norm of the derivs vector  [[dy]]_2/[[y]_2
        """
        t = 0  # dummy
        dy = self.derivs(t, y)

        return calc_norm(dy)/calc_norm(y)



    
class Simulator(object):
    def __init__(self, stT, endT):
        self._stT = stT    # start time of simulation
        self._endT = endT  # end time of simulation
        
        self._des_list = []
        self._EVA_list = []        # 全EVAのリスト
        self._dep_list = []

        self._lam = 5      # EVの発生頻度
        self._lamda = 0.1
        
        self._sol = None   # time series of states
        self._opt = None   # convergence values of states

        self._EVA_id = None
        
        self._G = None
        

    def add_des(self, Destination):  # 出発地点のリスト
        self._des_list.append(Destination)
    
    def add_EVA(self, EVA):
        self._EVA_list.append(EVA)

    def add_dep(self, Departure):  # 目的地のリスト
        self._dep_list.append(Departure)


    def create_graph(self, query):
        # 道路グラフネットワーク取得
        graphml_outfile = "road_network.graphml"
        if not os.path.isfile(graphml_outfile):
            # 走行可能な道路グラフネットワークを取得
            self._G = ox.graph_from_place(query, network_type = "drive")
            # 取得データを再利用目的でGraphml形式にて保存
            ox.save_graphml(self._G, filepath = graphml_outfile)
        else:
            # 前回取得の道路グラフネットワークを再利用
            self._G = ox.load_graphml(graphml_outfile)

            
    def all_get_id(self):  # 全てのidをGに格納しておく
        for EVA in self._EVA_list:
            point = (EVA._lat, EVA._lon)
            id = ox.get_nearest_node(self._G, point)
            EVA.set_id(id)
            
        for des in self._des_list:
            point = (des._lat, des._lon)
            id = ox.get_nearest_node(self._G, point)
            des.set_id(id)

    
    def list_gen(self, pop_list):       
        list_pop = [dep._pop for dep in pop_list]
        
        return list_pop
            
    
    def random_des_choice(self):  # 目的地リストから一つの目的地を選ぶ
        des_pop = self.list_gen(self._des_list)
        des_choice = random.choices(self._des_list, k = 1, weights = des_pop)

        return des_choice[0]

    
    def get_shortest_path(self, EV):
        start = EV                            # 出発地点の選択
        end = self.random_des_choice()        # 目的地の選択
        print(end._place_id)
        print(start._place_id)
        
        path = ox.shortest_path(self._G, start._place_id, end._place_id)  # 最短パスを求めている

        return path


    def pickup_EVA(self, EV):                # 経路から範囲内にあるEVAを抽出する
        EVA_id_list = []
        path = self.get_shortest_path(EV)    # 経路を取得
        
        for load in path:                    # 経路から100ｍ以内のEVAをpickup
            for EVA in self._EVA_list:
                dis = round(nx.shortest_path_length(self._G, EVA._place_id, load, weight = 'length'))
                if dis <= 1000:
                    EVA_id_list.append(EVA._id)

                    
        for EVA in self._EVA_list:       # 目的地近くのEVAを抽出
            dis = round(nx.shortest_path_length(self._G, EVA._place_id, path[-1], weight = 'length'))
            EV._dis_list.append(dis)
            if dis <= 1000:
                EVA_id_list.append(EVA._id)     
             
        return list(set(EVA_id_list))



    def evol(self, init) :
        """
        obtain the time series of states using Scipy's funcition 'solve_ivp'
        """
        self._sol = solve_ivp(self.derivs, (self._stT, self._endT),
                              init, dense_output = True, method='Radau')
               
    def rnd_exp(self):
        u = random.random()
        x = (-1 / self._lam)*math.log(1 - u)

        return x


    def calc_v(self, EV):
        v_cal = 0
        self.v_list = []
        for eva in self._EVA_list:
            if EV._kind == "B":
                v_cal = (-eva._kappa_dis * eva._dis
                         -eva._kappa_price_b * eva._EV_list[1]._price_rate)
                self.v_list.append(v_cal)

            elif EV._kind == "S":
                v_cal = (-eva._kappa_dis * eva._dis
                         +eva._kappa_price_s * eva._EV_list[0]._price_rate)
                self.v_list.append(v_cal)

        self.calc_pro()

        
    def calc_pro(self):
        all = 0
        for i in self.v_list:
            all += math.exp(self._lamda*i)
        self._pr = [math.exp(self._lamda*j) / all for j in self.v_list]

        self.EVA_choise()

        
    def EVA_choise(self):   # 多項式モデルの確率を元に得た確率からEVAを選択する
        print(self._pr)
        pickup_EVA = random.choices(self._EVA_list, k = 1, weights = self._pr)
        self._EVA_id = pickup_EVA[0]._id
        print("選択したEVA = {0}".format(self._EVA_id))

            
    def calc_all(self, t):
        for eva in self._EVA_list:
            eva.set_init(init_x, init_p)
            eva.get_conv(t)


    def next_dep_calc(self):
        ev_min = EV(id = 0, kind = "S")
        ev_min._depT = 100
        for eva in self._EVA_list:      # 次に出発するEVの時間を計算
            for ev in eva._EV_list.values():
                if ev._depT < ev_min._depT:
                    ev_min = ev
                    self._EVA_id = eva._id

        return ev_min

    
    def dep_EV_pro(self, EVA_id, EV_id):  # 出発するEVの出発処理
        del self._EVA_list[EVA_id]._EV_list[EV_id]


    


def calc_norm(vec) :
    """
      calculate the 2nd norm of vector
    """
    norm = 0.0
    for v in vec:
        norm += v*v
        
    return math.sqrt(norm)


def select_kind():
    k = random.random()
    if k >= 0.5:  kind = "S"
    else:         kind = "B"

    return kind


def select_place(data):
    weight = [d[2] for d in data]
    pickup_EV_place = random.choices(data, k = 1, weights = weight)
    
    return pickup_EV_place[0]


def make_EVA(sim, data):
    for i,d in enumerate(data):
        eva = EVA(id = i)
        eva.set_param(k1 = 0.1, k2 = 0.1, k3 = 0.1, limit_As = 64,limit_Ar = 64, rs = 1, rb = 1)
        eva.set_place(latitude = d[0], longitude = d[1], population = d[2])
        sim.add_EVA(eva)
        sim._EVA_list[i].set_init(init_x, init_p)       # 初期化
        make_first_EV(eva)                 # 常に買い手，売りてEVは存在しなければならない


def make_first_EV(eva):
    seller = EV(id = 0, kind = "S")
    seller.set_time(arrT = stT, depT = endT, t_a = stT)
    seller.set_calc_param(gamma = alpha, kappa_r = 0.1, base_p = 15,Es = 10000, Eb = 0)
    seller._price_rate = 50
    eva.add_EV(seller)

    buyer = EV(id = 1, kind = 'B')
    buyer.set_time(arrT = stT, depT = endT, t_a = stT)
    buyer.set_calc_param(gamma = beta, kappa_r = 0.1, base_p = 16, Es = 0, Eb = 10000)
    buyer._price_rate = 25
    eva.add_EV(buyer)

    
def make_EV(sim, t, i, kind, place):
    if kind == "S":
        ev = EV(id = i, kind = "S")
        ev.set_time(arrT = t, depT = t + 50, t_a = t)
        ev.set_calc_param(gamma = alpha, kappa_r = 0.1, base_p = 15, Es = 17, Eb = 0)
        ev.set_place(latitude = place[0], longitude = place[1], population = place[2], sim = sim)
        #sim._EVA_list[sim._EVA_id].add_EV(seller)
        #sim._EVA_list[sim._EVA_id]._s_num += 1
        
    elif kind == "B":
        ev = EV(id = i, kind = "B")
        ev.set_time(arrT = t, depT = t + 50, t_a = t)
        ev.set_calc_param(gamma = beta, kappa_r = 0.1, base_p = 16, Es = 0, Eb = 17)
        ev.set_place(latitude = place[0], longitude = place[1], population = place[2], sim = sim)
        #sim._EVA_list[sim._EVA_id].add_EV(buyer)
        #sim._EVA_list[sim._EVA_id]._b_num += 1

    return ev
        

        
def print_EV_rate(sim):
    for eva in sim._EVA_list:
        for ev in eva._EV_list.values():
            if ev._kind == "S":
                print("EVA{3} , kind: {0} , id: {1} , rate: {2}"
                      .format(ev._kind, ev._id, ev._rate, eva._id))

    for ev in eva._EV_list.values():
        if ev._kind == "B":
            print("EVA:{3}, kind: {0} , id: {1} , rate: {2}"
                  .format(ev._kind, ev._id, ev._rate, eva._id))
    print()

    
def print_EV_num(sim):
    for eva in sim._EVA_list:
        print("EVA {0}, S_num = {1}, Bnum = {2}"
              .format(eva._id, eva._s_num, eva._b_num))

        
def print_EV_price_rate(sim):
    for eva in sim._EVA_list:
        for ev in eva._EV_list.values():
            print("EVA{0}, kind: {1}, id: {2} , rate: {3} , E_now:{4},price:{5}, price_pre:{6}, price_rate:{7}".format(eva._id, ev._kind, ev._id, ev._rate,ev._E_now, ev._price, ev._price_pre, ev._price_rate))


def read_csv(file):  # ファイルの読み込み
    data = []
    for line in open(file, 'r'):
        lat, lon, pop = map(float, line.split(","))
        data.append([lat, lon, pop])
     
    return data


def make_des(sim, data):
    for d in data:
        des = Destination()
        des.set_place(latitude = d[0], longitude = d[1], population = d[2])
        sim.add_des(des)


            
    
def main():
    place = "Sanda,Hyogo,Japan"

    shop_list = read_csv("Sanda_shop_list_all.csv")
    EVA_list = read_csv("Sanda_parking_list_2.csv")
    house_list = read_csv("Sanda_population_uddy.csv")

    EVA_num = len(EVA_list)         # EVAの台数
    
    sim = Simulator(stT = stT, endT = endT)
    make_EVA(sim = sim, data = EVA_list)
    make_des(sim = sim, data = shop_list)

    sim.create_graph(place)
    sim.all_get_id()
   
    next_arr_time = sim.rnd_exp()
    next_dep_time = endT  

    i = 2               # EVの数
    t = 0                 # 現在の時刻

    while (t < endT):
        if (next_arr_time < next_dep_time):
            t = next_arr_time

            EV_kind = select_kind()                    # 生成するEVがSかBのどちらかを選択
            EV_place = select_place(house_list)             
            EV = make_EV(sim = sim, t = t, i = i, kind = EV_kind, place = EV_place)
            EVA_candidacy = sim.pickup_EVA(EV)         # EVAの行き先候補
            
            sim.calc_v(EV)                             # ここで売買するEVAを選択している     
            i += 1

            print_EV_num(sim)
            
            sim.calc_all(t)                       # 全部を計算し直している

            
            next_dep_EV = sim.next_dep_calc()     # 次に出発するEVを格納
            next_dep_time = next_dep_EV._depT     # 次に出発するEVの出発時間をnext_dep_timeに格納
            next_arr_time += sim.rnd_exp()        # 次にEVAに到着する時間を計算

        else:
            t = next_dep_time                    
           
            sim.dep_EV_pro(sim._EVA_id, next_dep_EV._id)   # 出発処理        

            sim.calc_all(t)                                # 出発したあとの全体の計算

            
            next_dep_EV = sim.next_dep_calc()              # 次に出発するEVを計算
            next_dep_time = next_dep_EV._depT              # 次に出発するEVの出発時間

        print_EV_price_rate(sim)

            
if __name__ == "__main__":
    main()
        
