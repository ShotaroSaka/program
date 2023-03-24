import sys
import math
import numpy as np
from scipy.integrate import odeint
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

import random
random.seed(2)

stT = 0             # 開始時間
endT = 6            # 終了時間

init_x = 1.0        # initial rates of EVs
init_p = 0.0        # initial price→pena

alpha = 2           ## parameter setting for ev # parameter of the utility function for buyers 
beta = 2



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


    def set_EVA_candidate(self, EVA_candidate):
        self.EVA_can = EVA_candidate  # 候補のEVAidと距離の集合（辞書型）

        
    def set_calc_param(self, gamma, kappa_r, base_p, Es, Eb) :
        self._gamma = gamma         # parameter of the utility function
        self._kappa_r = kappa_r     # coefficient used in the derivs
        self._base_p = base_p       # base line of price

        self._Es = Es               
        self._Eb = Eb
        self._E_now = 0             # 今まで取引した電力量
        self._rate = None           # EViに流れている電力レート
        self._gamma_fact = 2        # 価格の計算式に用いられているガンマ
        self._EVA_id = None

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
                                * rate**(self._gamma_fact)*(p[0] - p[2])) / rate   # 価格決定式
            
        elif self._kind == 'B' :  # for buyers
            self._price += (self._kappa_b * rate**(self._gamma_fact)
                            * (p[1] + p[2]) * (t1 - self._t_a))

            self._price_pre = (self._price + (self._kappa_b * rate**(self._gamma_fact)
                               * (p[1] + p[2]) * (self._depT - t1))) 

            self._price_rate = (rate*self._base_p + self._kappa_b
                                *rate**(self._gamma_fact)*(p[1] + p[2])) / rate   # 価格決定式

            
    def calc_E_now(self, rate, t1):  # 完了した電力量
        self._E_now += rate*(t1 - self._t_a)
    


    
class EVA(object) :
    def __init__(self, id) :
        self._id = id
        self._EV_list = {}

        
    def set_param(self, k1, k2, k3, limit_As, limit_Ar, weight) :
        self._k1 = k1                  # EVAkでのペナルティ
        self._k2 = k2
        self._k3 = k3
        
        self._kappa_dis = 1            # 多項ロジットモデルでの重み（距離）
        self._kappa_price_s = weight      # 多項ロジットモデルでの重み（売り手の値段）
        self._kappa_price_b = weight     # 多項ロジットモデルでの重み（買い手の値段）

        self._limit_As = limit_As      # ケーブル容量
        self._limit_Ar = limit_Ar
        
        self._s_num = 1                # EViにいる売り手EVの数
        self._b_num = 1                # EViにいる買い手EVの数


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

        self._EVA_list = []        # 全EVAのリスト
        
        self._sol = None   # time series of states
        self._opt = None   # convergence values of states

        self._EVA_id = None

        self._lam = 5      # EVの発生頻度
        self._lamda = 0.1

        
    def add_EVA(self, EVA):
        self._EVA_list.append(EVA)


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
        plice_rate = []
        EVA_place = []
        EVA_id = []
        if EV._kind == "B":
            for eva_id, eva_dis in EV.EVA_can.items():
                v_cal = (-self._EVA_list[eva_id]._kappa_dis * (eva_dis*0.05)
                         -self._EVA_list[eva_id]._kappa_price_b
                         * self._EVA_list[eva_id]._EV_list[1]._price_rate)
                self.v_list.append(v_cal)
                plice_rate.append(self._EVA_list[eva_id]._EV_list[1]._price_rate)
                EVA_place.append(eva_dis)
                EVA_id.append(eva_id)

        elif EV._kind == "S":
            for eva_id, eva_dis in EV.EVA_can.items():
                v_cal = (-self._EVA_list[eva_id]._kappa_dis * (eva_dis*0.05)
                         +self._EVA_list[eva_id]._kappa_price_s
                         *self._EVA_list[eva_id]._EV_list[0]._price_rate)
                self.v_list.append(v_cal)
                plice_rate.append(self._EVA_list[eva_id]._EV_list[1]._price_rate)
                EVA_place.append(eva_dis)
                EVA_id.append(eva_id)

        print("それぞれのEVAのid  : ", end ="")
        print(EVA_id)
        print("それぞれのEVAの距離: ", end ="")
        print(EVA_place)
        print("それぞれのEVAの価格: ", end ="")        
        print(plice_rate)
        print("それぞれのEVAの効用: ", end ="")        
        print(self.v_list)
        

                         
        
    def calc_pro(self, EV):
        all = 0
        for i in self.v_list:
            all += math.exp(self._lamda*i)
        self._pr = [math.exp(self._lamda*j) / all for j in self.v_list]

        
    def EVA_choise(self, EV):   # 多項式モデルの確率を元に得た確率からEVAを選択する
        self.calc_v(EV)
        self.calc_pro(EV)
        EVA_can_id = [i for i in EV.EVA_can]
        pickup_EVA = random.choices(EVA_can_id, k = 1, weights = self._pr)
        self._EVA_id = pickup_EVA[0]
        EV._EVA_id = pickup_EVA[0]
        self.print_EVA_choise()

        return self._EVA_id

            
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


    def print_EVA_choise(self):
        print("それぞれのEVAの確率: ", end = "")
        print(self._pr)
        print("選択したEVA: {0}".format(self._EVA_id))
       
                        


    


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
       

def make_EVA(EVA_num, sim, k):
    for i in range(EVA_num):
        eva = EVA(id = i)
        eva.set_param(k1 = 0.1, k2 = 0.1, k3 = 0.1, limit_As = 64, limit_Ar = 64, weight = k)
        sim.add_EVA(eva)
        sim._EVA_list[i].set_init(init_x, init_p)       # 初期化
        make_first_EV(eva)                 # 常に買い手，売りてEVは存在しなければならない


def make_first_EV(eva):
    seller = EV(id = 0, kind = "S")
    seller.set_time(arrT = stT, depT = endT, t_a = stT)
    seller.set_calc_param(gamma = alpha, kappa_r = 0.1, base_p = 10,Es = 10000, Eb = 0)
    seller._price_rate = 50
    eva.add_EV(seller)

    buyer = EV(id = 1, kind = 'B')
    buyer.set_time(arrT = stT, depT = endT, t_a = stT)
    buyer.set_calc_param(gamma = beta, kappa_r = 0.1, base_p = 20, Es = 0, Eb = 10000)
    buyer._price_rate = 25
    eva.add_EV(buyer)

    
def make_EV(i, sim, kind, t, EVA_candidate):
    if kind == "S":
        ev = EV(id = i, kind = "S")
        ev.set_time(arrT = t, depT = t + 50, t_a = t)
        ev.set_calc_param(gamma = alpha, kappa_r = 0.1, base_p = 10, Es = 20, Eb = 0)
        ev.set_EVA_candidate(EVA_candidate)
        
    elif kind == "B":
        ev = EV(id = i, kind = "B")
        ev.set_time(arrT = t, depT = t + 50, t_a = t)
        ev.set_calc_param(gamma = beta, kappa_r = 0.1, base_p = 20, Es = 0, Eb = 20)
        ev.set_EVA_candidate(EVA_candidate)
        
    return ev


def print_next_event_time(next_arr_time,next_dep_time):
  print("next_arr_time: {0} next_dep_time: {1}".format(next_arr_time,next_dep_time))

        
def print_EV_rate(sim):
    for eva in sim._EVA_list:
        for ev in eva._EV_list.values():
            if ev._kind == "S":
                print("EVA: {3} kind: {0} id: {1} rate: {2}"
                      .format(ev._kind, ev._id, ev._rate, eva._id))

    for ev in eva._EV_list.values():
        if ev._kind == "B":
            print("EVA: {3} kind: {0} id: {1} rate: {2}"
                  .format(ev._kind, ev._id, ev._rate, eva._id))
    print()

    
def print_EV_num(sim):
    for eva in sim._EVA_list:
        print("EVA: {0} S_num: {1} Bnum: {2}"
              .format(eva._id, eva._s_num, eva._b_num))

        
def print_EV_price_rate(sim):
    for eva in sim._EVA_list:
        for ev in eva._EV_list.values():
            print("EVA: {0} kind: {1} id: {2} rate: {3} E_now: {4} price: {5} price_pre: {6} price_rate: {7}"
                  .format(eva._id, ev._kind, ev._id, ev._rate,ev._E_now, ev._price, ev._price_pre, ev._price_rate))
    print()



def print_dep_list(dep_list):
    print("dep_EV_list")
    for ev in dep_list:
        print(" EVA: {7} id: {0} kind: {1} gamma: {6} arrT: {2} depT: {3} totalT: {4} price: {5}"
              .format(ev._id,ev._kind,ev._arrT, ev._depT,ev._depT - ev._arrT, ev._price, ev._gamma, ev._EVA_id ))


            
def read_csv(file):  # ファイルの読み込み
    EVA_candidate_list = []
    for line in open(file, 'r'):
        data = list(map(int, line.split(",")))
        EVA_data = {}

        j = int(len(data)/2)
        for i in range(j):
            EVA_data.update({data[i]: data[j + i]})
        EVA_candidate_list.append(EVA_data)

    return EVA_candidate_list
            
   
    
def main():
    EVA_candidate_list = read_csv("Sanda_EVA_candidate.csv")
    EVA_num = 7         # EVAの台数
    
    sim = Simulator(stT = stT, endT = endT)
    k = int(sys.argv[1])
    make_EVA(EVA_num, sim, k)

    next_arr_time = sim.rnd_exp()
    next_dep_time = endT  

    EV_num = 2               # EVの数
    t = 0                 # 現在の時刻
    i = 0

    dep_ev_list = []

    while (t < endT):
        if (next_arr_time < next_dep_time):
            t = next_arr_time
            print("Event arrT: {0}".format(t))
            
            sim.calc_all(t)                       # 追加したので，全部を計算し直している
            kind = select_kind()                                # 生成するEVがSかBのどちらかを選択
            EVA_candidate = EVA_candidate_list[i]               # A(i)：EVAのidと距離，辞書型として格納
            EV = make_EV(EV_num, sim, kind, t, EVA_candidate)   # EVを作成
            EV_num += 1
            
            pickup_EVA_id = sim.EVA_choise(EV)                    # ここで売買するEVAを選択している
            sim._EVA_list[pickup_EVA_id].add_EV(EV)               # EVAに追加
            
            if EV._kind == "S":
                sim._EVA_list[pickup_EVA_id]._s_num += 1
            elif EV._kind == "B":
                sim._EVA_list[pickup_EVA_id]._b_num += 1

            
            print_EV_num(sim)            
            sim.calc_all(t)                       # 追加したので，全部を計算し直している

            
            next_dep_EV = sim.next_dep_calc()     # 次に出発するEVを格納
            next_dep_time = next_dep_EV._depT     # 次に出発するEVの出発時間をnext_dep_timeに格納
            next_arr_time += sim.rnd_exp()        # 次にEVAに到着する時間を計算

            print_next_event_time(next_arr_time, next_dep_time)

        else:
            t = next_dep_time
            print("Event depT: {0}".format(t))
            
            sim.calc_all(t)                                # 出発したあとの全体の計算
            if sim._EVA_list[sim._EVA_id]._EV_list[next_dep_EV._id]._kind == "S":
                sim._EVA_list[sim._EVA_id]._s_num -= 1
            elif sim._EVA_list[sim._EVA_id]._EV_list[next_dep_EV._id]._kind == "B":
                sim._EVA_list[sim._EVA_id]._b_num -= 1                

            dep_ev_list.append(sim._EVA_list[sim._EVA_id]._EV_list[next_dep_EV._id])
            sim.dep_EV_pro(sim._EVA_id, next_dep_EV._id)   # 出発処理

            print_next_event_time(next_arr_time,next_dep_time)
            print_EV_num(sim)            
            sim.calc_all(t)                                # 出発したあとの全体の計算

            
            next_dep_EV = sim.next_dep_calc()              # 次に出発するEVを計算
            next_dep_time = next_dep_EV._depT              # 次に出発するEVの出発時間
           
        print_EV_price_rate(sim)
        i += 1

    print_dep_list(dep_ev_list)

            
if __name__ == "__main__":
    main()
        
