#!/usr/bin/env python3
import sys
import math

from scipy.integrate import odeint
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

import random
random.seed(2)


class EV(object) :
    def __init__(self, id, kind = None):
        self._id = id                                       # identification number of the EV group
        self._kappa_s = 100                                # 売電価格の計算式における係数
        self._kappa_b = 100                                # 買電価格の計算式における係数

        if kind == None:   self._kind = self.set_kind()     # kind of EVs (kind = 'S' or kind = 'B') in the group
        else:              self._kind = kind

        
    def set_time(self, arrT, depT, t_a) -> None:
        self._arrT = arrT         # arrival time of EV
        self._depT = depT         # departure time of EV
        self._t_a = t_a           # 現在の時間をもたせる


    def set_EVA_candidate(self, EVA_candidate) -> None:
        self.EVA_can = EVA_candidate     # 候補の EVA_idと距離の集合（辞書型）

        
    def set_kind(self) -> str:           # EV の種類を決定（"S" or "B"）
        k = random.random()
        if k >= 0.5:  kind = "S"
        else:         kind = "B"

        return kind

        
    def set_calc_param(self, kappa_r, base_p, Es, Eb) -> None:
        self._gamma = 2             # parameter of the utility function
        self._kappa_r = kappa_r     # coefficient used in the derivs
        self._base_p = base_p       # base line of price

        self._Es = Es               
        self._Eb = Eb
        self._E_now = 0             # 今まで取引した電力量
        self._gamma_fact = 2        # 価格の計算式に用いられているガンマ
        self._rate = None

        self._price = 0             # 電力売買価格   

        
    def derivs_util(self, x) :
        return (x + 1)**(-self._gamma)   # differential equation of the utility function

    
    def derivs_x(self, x, p) :
        return self._kappa_r*(self.derivs_util(x) - p*x)  # differential equation of the rate

    
    def calc_price(self, rate, p, t1) -> None:
        if self._kind == "S":    # for sellers
            p = self._kappa_s * rate**(self._gamma_fact) * (p[0]-p[2])
            self._price += rate*(t1 - self._t_a)*self._base_p - p*(t1 - self._t_a)        # 今まで取引した価格    
            self._price_rate = (rate*self._base_p - p) / rate                             # 1 kWh あたりの値段
            self._price_pre = self._price + (self._Es - self._E_now)*self._price_rate     # 混雑状況が一定のときの値段
            
        elif self._kind == "B":  # for buyers
            p = self._kappa_b * rate**(self._gamma_fact) * (p[1]+p[2])
            self._price += rate*(t1 - self._t_a)*self._base_p + p*(t1 - self._t_a)
            self._price_rate = (rate*self._base_p + p) / rate 
            self._price_pre = self._price + (self._Eb - self._E_now)*self._price_rate 
           
            
    def calc_E_now(self, rate, t1) -> None:  # 完了した電力量
        self._E_now += rate*(t1 - self._t_a)
    


        
class EVA(object) :
    def __init__(self, id) :
        self._id = id
        self._EV_list = {}

        
    def set_param(self, k1, k2, k3, limit_As, limit_Ar, kappa) -> None:
        self._k1 = k1                  # EVA_k でのペナルティ
        self._k2 = k2
        self._k3 = k3
        
        self._kappa_dis = 1            # 多項ロジットモデルでの重み（距離）
        self._kappa_price = kappa      # 多項ロジットモデルでの重み（値段）
        
        self._limit_As = limit_As      # ケーブル容量
        self._limit_Ar = limit_Ar
        
        self._s_num = 1                # EVA_k にいる売り手 EV の数
        self._b_num = 1                # EVA_k にいる買い手 EV の数

        self._init_x = 1.0
        self._init_p = 0.0


    def add_EV(self, EV) -> None:
        self._EV_list[EV._id] = EV
   
        
    def derivs_p1(self, As) :
        return self._k1*(As - self._limit_As)
    
    def derivs_p2(self, Ar) :
        return self._k2*(Ar - self._limit_Ar)

    def derivs_p3(self, As, Ar) :
        return self._k3*(Ar - As)

    
    def derivs_p(self, As, Ar, p1, p2, p3) -> list:
        dp1 = self.derivs_p1(As)
        dp2 = self.derivs_p2(Ar)
        dp3 = self.derivs_p3(As, Ar)

        return [dp1, dp2, dp3]

    
    def calc_depT(self, rate) -> None:    # 電力売買が完了する時間を計算
        for ev in self._EV_list.values():
            if ev._kind == "S":
                ev._depT = ev._t_a + (ev._Es - ev._E_now)/rate
                
            elif ev._kind == "B":
                ev._depT = ev._t_a + (ev._Eb - ev._E_now)/rate

        
    def calc_init(self) -> None:
        self._init = [self._init_x]*len(self._EV_list) + [self._init_p]*3


    def get_conv(self, e_time) -> None:
        self._opt = minimize(self.norm_derivs, self._init)   # その時のレートとペナルティを計算
        EV_n = len(self._EV_list)
        x = {}

        p1 = self._opt.x[EV_n]
        p2 = self._opt.x[EV_n + 1]
        p3 = self._opt.x[EV_n + 2]

        i = 0
        for ev in self._EV_list.values():
            x[i] = self._opt.x[i]                       # レート of EV id
            ev._rate = x[i]

            ev.calc_price(x[i], (p1, p2, p3), e_time)   # 価格を更新する（etimeまでの合計価格）
            ev.calc_E_now(x[i], e_time)                 # etime までの総充電量
            ev._t_a = e_time                            # 今の時間を保存する

            self.calc_depT(x[i])                        # レートと enow が更新されたので，depT を計算する

            i += 1

            
    def derivs(self, t, y):
        """
           calculate
        """ 
        ## calculate the both aggregate rates of sellers and buyers.
        As = Ar = 0.0
        i = 0
        for ev in self._EV_list.values():
            if ev._kind == "S":    As += y[i]
            elif ev._kind == "B":  Ar += y[i]
            else :                assert(False)
        
            i += 1
            
        ## get price
        p1 = y[i]
        p2 = y[i+1]
        p3 = y[i+2]

        ## calculate the derivs of stats
        dy = []
        i = 0
        for ev in self._EV_list.values():
            x = y[i]
            if ev._kind == "S":    p = p1 - p3
            elif ev._kind == "B":  p = p2 + p3
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
        self._stT = stT                # start time of simulation
        self._endT = endT              # end time of simulation

        self._lam = 5                 # EV の発生頻度 23, 28
        self._lamda = 0.5              # 多項ロジットモデルでのランダム性の大きさ

        self._sol = None               # time series of states
        self._opt = None               # convergence values of states

        self._EVA_list = []            # 全EVAのリスト
        self._EVA_candidate_list = []  
        self.dep_ev_list = []          # 出発したEVのリスト
        

    def add_EVA(self, EVA) -> None:
        self._EVA_list.append(EVA)

               
    def rnd_exp(self):
        u = random.random()
        x = (-1 / self._lam)*math.log(1 - u)

        return x


    def calc_v(self, EV) -> None:
        self.v_list = []
        self.EVA_price = []
        self.EVA_place = []
        self.EVA_id = []
        v_cal = 0
        for eva_id, eva_dis in EV.EVA_can.items():
            if EV._kind == "S":
                kappa_price = self._EVA_list[eva_id]._kappa_price                
                kappa_dis = self._EVA_list[eva_id]._kappa_dis
                price_rate = self._EVA_list[eva_id]._EV_list[0]._price_rate
            elif EV._kind == "B":                
                kappa_price = -self._EVA_list[eva_id]._kappa_price
                kappa_dis = self._EVA_list[eva_id]._kappa_dis
                price_rate = self._EVA_list[eva_id]._EV_list[1]._price_rate

            v_cal = -kappa_dis*(eva_dis*0.05) + kappa_price*price_rate   # 多項ロジットモデル

            self.v_list.append(v_cal)
            self.EVA_id.append(eva_id)
            self.EVA_place.append(eva_dis)
            self.EVA_price.append(price_rate)
                                               
       
    def calc_pro(self, EV) -> None:
        all = 0
        for i in self.v_list:
            all += math.exp(self._lamda*i)
        self._pr = [math.exp(self._lamda*j) / all for j in self.v_list]

        
    def choice_EVA(self, EV):            # 確率をもとに EVA を選択する
        self.calc_v(EV)
        self.calc_pro(EV)
        EVA_can_id = [i for i in EV.EVA_can]
        pickup_EVA = random.choices(EVA_can_id, k = 1, weights = self._pr)
        self._EVA_id = EV._EVA_id = pickup_EVA[0]
        self.print_calc_comfirmation()
      
        return self._EVA_id

            
    def calc_all(self, t) -> None:
        for eva in self._EVA_list:
            eva.calc_init()
            eva.get_conv(t)


    def calc_next_dep(self) -> object:   # 次に出発するEVの時間を計算
        ev_min = EV(id = 0)
        ev_min._depT = 100
        for eva in self._EVA_list:     
            for ev in eva._EV_list.values():
                if ev._depT < ev_min._depT:
                    ev_min = ev
                    self._EVA_id = eva._id

        return ev_min

    
    def process_dep_EV(self, EVA_id, EV_id) -> None:  # 出発するEVの出発処理
        EV = self._EVA_list[EVA_id]._EV_list.pop(EV_id)
        self.dep_ev_list.append(EV)

        
    def read_csv(self, file) -> None:  # ファイルの読み込み
        for line in open(file, "r"):
            EVA_data = {}
            data = list(map(int, line.split()))

            j = int(len(data)/2)
            for i in range(j):
                EVA_data.update({data[i]: data[j + i]})
            self._EVA_candidate_list.append(EVA_data)


    def EVA_candidate_generator(self):
        for EVA_candidate in self._EVA_candidate_list: 
            yield EVA_candidate

            
    def print_calc_comfirmation(self) -> None:
        for id, dis, price, V ,p in zip(self.EVA_id, self.EVA_place,self.EVA_price, self.v_list, self._pr):
            print("EVA_id: {0} dis: {1} price: {2} V: {3} pr: {4}"
                  .format(id, dis, round(price, 3), round(V, 3), round(p, 3)))
        print("選択したEVA: {0}".format(self._EVA_id))
        
        
    def print_EV_num(self) -> None:
        for eva in self._EVA_list:
            print("EVA: {0} S_num: {1} Bnum: {2}"
                  .format(eva._id, eva._s_num, eva._b_num))

            
    def print_EV_price_rate_1(self) -> None:
        for eva in self._EVA_list:
            for ev in eva._EV_list.values():
                print("EVA: {0} kind: {1} id: {2} rate: {3} E_now: {4} price: {5} price_pre: {6} price_rate: {7}"
                      .format(eva._id, ev._kind, ev._id, round(ev._rate, 2), round(ev._E_now, 2), round(ev._price, 3), round(ev._price_pre, 3), round(ev._price_rate, 3)))            
        print()

        
    def print_EV_price_rate_2(self) -> None:
        for eva in self._EVA_list:
            for ev in eva._EV_list.values():
                if ev._id != 0 and ev._id != 1:
                    print("EVA: {0} kind: {1} id: {2} rate: {3} E_now: {4} price: {5} price_pre: {6} price_rate: {7}"
                          .format(eva._id, ev._kind, ev._id, round(ev._rate, 2), round(ev._E_now, 2), round(ev._price, 3), round(ev._price_pre, 3), round(ev._price_rate, 3)))            
                else:
                    continue                    
        print()


    def print_dep_list(self) -> None:
        print("dep_EV_list")
        for ev in self.dep_ev_list:
            print("EVA: {0} id: {1} kind: {2} gamma: {3} arrT: {4} depT: {5} totalT: {6} price: {7}"
                  .format(ev._EVA_id, ev._id, ev._kind, ev._gamma, ev._arrT, ev._depT, ev._depT - ev._arrT, ev._price))
        self.print_ev_price_ave()


    def print_ev_price_ave(self) -> None:
        i = 0
        j = 0
        S_sum = 0
        B_sum = 0 
        for ev in self.dep_ev_list:
            if ev._kind == "S":
                S_sum += ev._price
                i += 1
            elif ev._kind == "B":
                B_sum += ev._price
                j += 1
        S_ave = S_sum / i
        B_ave = B_sum / j
        print("S_num: {0} S_ave_price: {1} B_num: {2} B_ave_price: {3}".format(i, S_ave, j, B_ave))
        
        
        

def calc_norm(vec) :
    """
      calculate the 2nd norm of vector
    """
    norm = 0.0
    for v in vec:
        norm += v*v
        
    return math.sqrt(norm)
       

def make_EVA(EVA_num, sim, price_kappa):
    for i in range(EVA_num):
        eva = EVA(id = i)
        eva.set_param(k1 = 0.1, k2 = 0.1, k3 = 0.1,
                      limit_As = 64, limit_Ar = 64, kappa = price_kappa) 
        sim.add_EVA(eva)
        make_first_EV(eva, sim)            # 常に買い手，売り手 EV は存在


def make_first_EV(eva, sim):
    seller = EV(id = 0, kind = "S")
    seller.set_time(arrT = sim._stT, depT = sim._endT, t_a = sim._stT)
    seller.set_calc_param(kappa_r = 0.1, base_p = 15,Es = 10000, Eb = 0)
    eva.add_EV(seller)

    buyer = EV(id = 1, kind = "B")
    buyer.set_time(arrT = sim._stT, depT = sim._endT, t_a = sim._stT)
    buyer.set_calc_param(kappa_r = 0.1, base_p = 16, Es = 0, Eb = 10000)
    eva.add_EV(buyer)

    
def make_EV(i, time, EVA_can):
    ev = EV(id = i)
    ev.set_time(arrT = time, depT = time + 50, t_a = time)
    ev.set_EVA_candidate(EVA_can)
    if ev._kind == "S":
        ev.set_calc_param(kappa_r = 0.1, base_p = 15, Es = 17, Eb = 0)
    elif ev._kind == "B":
        ev.set_calc_param(kappa_r = 0.1, base_p = 16, Es = 0, Eb = 17)
        
    return ev


def print_next_event_time(next_arr_time, next_dep_time):
    print("next_arr_time: {0} next_dep_time: {1}".format(next_arr_time, next_dep_time))



    
def main():
    stT = 0              # 開始時間
    endT = 6             # 終了時間
    t = 0                # 現在の時刻
    sim = Simulator(stT = stT, endT = endT)
    sim.read_csv("easy_EVAnum:6.txt")
    #sim.read_csv("Sanda_EVA_candidate.txt")
    EVA_candidate = sim.EVA_candidate_generator()
    
    EV_num = 2                         # 初期の EV の数
    EVA_num = 6             # EVA の台数
    price_kappa = float(sys.argv[1])   # 多項ロジットモデルでの価格の重み
    make_EVA(EVA_num, sim, price_kappa)
    
    next_arr_time = sim.rnd_exp()
    next_dep_time = endT  
   
    while (t < endT):
        if (next_arr_time < next_dep_time):
            t = next_arr_time
            
            sim.calc_all(t)                                         # 追加したので，全て計算
            EV = make_EV(i = EV_num, time = t, EVA_can = EVA_candidate.__next__())        # EV を作成    
            EV_num += 1

            print("EV_kind: {0} Event arrT: {1} ".format(EV._kind, t))
            
            choice_EVA_id = sim.choice_EVA(EV)                      # 売買する EVA を選択
            sim._EVA_list[choice_EVA_id].add_EV(EV)                 # EVA に追加
            
            if EV._kind == "S":
                sim._EVA_list[choice_EVA_id]._s_num += 1
            elif EV._kind == "B":
                sim._EVA_list[choice_EVA_id]._b_num += 1
            
            sim.print_EV_num()            
            sim.calc_all(t)                       # 追加したので，全部を計算し直している

            
            next_dep_EV = sim.calc_next_dep()     # 次に出発する EV を格納
            next_dep_time = next_dep_EV._depT     # 次に出発する EV の出発時間を格納
            next_arr_time += sim.rnd_exp()        # 次に EVA に到着する時間を計算

            print_next_event_time(next_arr_time, next_dep_time)

        else:
            t = next_dep_time
            print("Event depT: {0}".format(t))
            
            sim.calc_all(t)

            if sim._EVA_list[sim._EVA_id]._EV_list[next_dep_EV._id]._kind == "S":
                sim._EVA_list[sim._EVA_id]._s_num -= 1
            elif sim._EVA_list[sim._EVA_id]._EV_list[next_dep_EV._id]._kind == "B":
                sim._EVA_list[sim._EVA_id]._b_num -= 1                

            sim.process_dep_EV(sim._EVA_id, next_dep_EV._id)   # 出発処理
            sim.print_EV_num()            
            sim.calc_all(t)                                    # 出発したあとの全体の計算

            
            next_dep_EV = sim.calc_next_dep()         # 次に出発する EV を計算
            next_dep_time = next_dep_EV._depT         # 次に出発する EV の出発時間

            print_next_event_time(next_arr_time, next_dep_time)
           
        sim.print_EV_price_rate_2()
    sim.print_dep_list()

            
if __name__ == "__main__":
    main()
        
