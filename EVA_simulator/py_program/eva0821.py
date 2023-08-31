#!/usr/bin/env python3
import sys
import math
import random
from scipy.optimize import minimize


class EV(object) :
    def __init__(self, id, kind = None):
        self._id = id                          # identification number of the EV group

        if kind == None:  self.set_kind()      # kind をランダムに設定
        else:             self._kind  = kind   # kind を指定して設定

        self._total_E_kWh = 0                  # 現在の電力売買量
        self._total_P_yen = 0                  # 現在の電力売買価格

        self._EVA_can = None                   # 行き先候補（辞書型）{id:dis, id:dis ・・ }
        self._EVA_id = None                    # 電力売買する EVA
     

    def set_kind(self) -> str:
        k = random.random()
        if k < 0.9:  kind = "S"
        else:        kind = "B"

        self._kind = kind


    def set_param_time(self, arrT, depT, nowT) -> None:
        self._arrT = arrT      # arrival time of EV
        self._depT = depT      # departure time of EV
        self._nowT = nowT      # now time of EV
        self._preT = None      # now time of EV


    def set_param_model(self, kappa_dis, kappa_P, kappa_nu):
        self._kappa_dis = kappa_dis    # 多項ロジットモデルでの距離の重み
        self._kappa_P   = kappa_P      # 多項ロジットモデルでの価格の重み
        self._kappa_nu  = kappa_nu     # 多項ロジットモデルでのランダム性の強さ


    def set_param_calc(self, alpha, base_P):
        self._alpha   = alpha         # parameter of the utility function
        self._gamma_r = 0.1           # coefficient used in the derivs            
        self._gamma_P = 100           # 電力価格の計算式における係数
        self._gamma_fact = 2          # 価格の計算式に用いられているガンマ

        self._base_P = base_P         # base line of price
        self._request_E_kWh = 17      # EV ユーザが取引したい電力量

        
    def set_EVA_candidate(self, EVA_candidate):
        self._EVA_can = EVA_candidate   # 候補の EVAid と距離の集合（辞書型）

        
    def derivs_util(self, x):
        return (x + 1)**(-self._alpha)   # differential equation of the utility function

    
    def derivs_x(self, x, p):
        return self._gamma_r*(self.derivs_util(x) - p*x)  # differential equation of the rate


    def set_P_now(self, p, nextT_h) -> None:
        # 前回計算してからの経過時間
        passedT = nextT_h - self._nowT

        # 売り手と買い手によって異なる計算式
        if self._kind == "S":
            tmp_p = -(p[0] - p[2])
        elif self._kind == "B":
            tmp_p =   p[1] + p[2]

        # 価格計算(1kWh あたりの価格，現在まで合計価格)
        p = self._gamma_P * self._E_rate_kW**(self._gamma_fact) * tmp_p
        self._P_rate = (self._E_rate_kW*self._base_P - p) / self._E_rate_kW        
        self._total_P_yen += self._E_rate_kW*passedT*self._base_P + p*passedT    
 

    def set_E_now(self, nextT_h) -> None:
        # 今まで取引した電力量
        self._total_E_kWh += self._E_rate_kW*(nextT_h - self._nowT)


    def calc_depT(self):
        self._preT = self._nowT + (self._request_E_kWh - self._total_E_kWh)/self._E_rate_kW
        
        


        
class EVA(object):
    def __init__(self, id):
        self._id = id
        self._EV_list = {}

        # EV の種類別にカウント
        self._S_EV_num = 0
        self._B_EV_num = 0
        
        # V 2 バッテリー → True
        # V 2 V          → False
        self._battery_exists = False
        # バッテリー容量  ※初期値は半分とする
        self._battery_kWh = 1000/2


    def set_param(self, limit_As, limit_Ar) -> None:
        # EVA k でのペナルティ
        self._k1 = 0.1                
        self._k2 = 0.1
        self._k3 = 0.1

        self._init_x = 1.0
        self._init_p = 0.0

        # ケーブル容量
        self._limit_As = limit_As      
        self._limit_Ar = limit_Ar


    def add_EV(self, ev) -> None:
        self._EV_list[ev._id] = ev
        self.EV_kind_counter(kind = ev._kind, count = 1)
        
        # バッテリーで電力売買している場合
        if self._battery_exists:
            # 電力売買する EV が見つかった場合にバッテリーを取り除く
            if self._EV_list[0]._kind == ev._kind:
                self.remove_battery()
        else:
            # 訪れた EV の電力売買を可能にするためバッテリーを追加
            if self._S_EV_num == 0:
                self.generate_battery(ev, kind = "S")
            elif self._B_EV_num == 0:
                self.generate_battery(ev, kind = "B")
            

    def remove_EV(self, ev) -> None:
        # dep_list を作成するため，popを使用し，出発する EV を返す
        dep_ev = self._EV_list.pop(ev._id)
        self.EV_kind_counter(kind = dep_ev._kind, count = -1)

        # バッテリーで電力売買している場合
        if self._battery_exists:
            # バッテリーだけが EVA 内にいるので取り除く
            if len(self._EV_list) == 1:                
                self.remove_battery()
        else:
            # 訪れた EV の電力売買を可能にするため EVA を追加
            if self._S_EV_num == 0:
                self.generate_battery(ev, kind = "S")
            elif self._B_EV_num == 0:
                self.generate_battery(ev, kind = "B")
                
        return dep_ev
        
    
    def generate_battery(self, ev, kind):
        eva_battery = EV(id = 0, kind = kind)
        eva_battery.set_param_time(arrT = ev._arrT, depT = 100, nowT = ev._nowT)
        eva_battery.set_param_calc(alpha = 2, base_P = 17)
        eva_battery._request_E_kWh = 500
        self._EV_list[eva_battery._id] = eva_battery
        self._battery_exists = True

        
    def remove_battery(self):
        eva_battery = self._EV_list.pop(0)
        self._battery_exists = False


    def EV_kind_counter(self, kind, count):
        if kind == "S":
            self._S_EV_num += count
        elif kind == "B":
            self._B_EV_num += count
        
    
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
    
            
    def get_conv(self, time) -> None:
        EV_n = len(self._EV_list)
        self._init = [self._init_x]*EV_n + [self._init_p]*3
        self._opt = minimize(self.norm_derivs, self._init)   # その時のレートとペナルティを計算
        
        p1 = self._opt.x[EV_n]
        p2 = self._opt.x[EV_n + 1]
        p3 = self._opt.x[EV_n + 2]


        EV_id = 0
        for ev in self._EV_list.values():
            ev._E_rate_kW = self._opt.x[EV_id]   # 新しく計算された電力レートをセット
            ev.set_P_now((p1, p2, p3), time)     # 現在までの電力売買価格を計算
            ev.set_E_now(time)                   # 現在までの電力売買価格を計算
            EV_id += 1

        # バッテリーの処理
        if self._battery_exists:
            eva_battery = self._EV_list[0]
            if eva_battery._kind == "S":
                self._battery_kWh -= eva_battery._E_rate_kW*(time - eva_battery._nowT)
            elif eva_battery._kind == "B":
                self._battery_kWh += eva_battery._E_rate_kW*(time - eva_battery._nowT) 

        # 時間設定
        for ev in self._EV_list.values():
            ev._nowT = time
            ev.calc_depT()            


            
    def get_P_rate(self, ev) -> None:
        EV_n = len(self._EV_list)
        self._init = [self._init_x]*EV_n + [self._init_p]*3
        self._opt = minimize(self.norm_derivs, self._init)   # その時のレートとペナルティを計算
        
        p1 = self._opt.x[EV_n]
        p2 = self._opt.x[EV_n + 1]
        p3 = self._opt.x[EV_n + 2]
      
        if ev._kind == "S":
            tmp_p = -(p1 - p3)
        elif ev._kind == "B":
            tmp_p =   p2 + p3

        
        # 新しく計算された電力レートをセット
        E_rate_kW = self._opt.x[EV_n - 1]
        p = ev._kappa_P * E_rate_kW**(ev._gamma_fact) * tmp_p
        P_rate = (E_rate_kW*ev._base_P - p) / E_rate_kW

        return P_rate


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
        self._stT = stT
        self._endT = endT

        self._EVA_list = []
        self._dep_ev_list = []
        self._EVA_candidate_list = []

        self._opt = None               # convergence values of states
        self._lam = 20                 # EV の発生頻度 23, 28


    def add_EVA(self, EVA) -> None:
        self._EVA_list.append(EVA)

        
    def rnd_exp(self):
        u = random.random()
        x = (-1/self._lam)*math.log(1 - u)

        return x

    
    def calc_all_EVA(self, time):
        for eva in self._EVA_list:
            if len(self._EVA_list[eva._id]._EV_list) > 0:
                self._EVA_list[eva._id].get_conv(time)

               
    def process_dep_EV(self, ev) -> None:  # 出発するEVの出発処理
        dep_ev = self._EVA_list[ev._EVA_id].remove_EV(ev)
        self._dep_ev_list.append(dep_ev)
        

    def select_EVA_and_add_EV(self, ev):      
        # 行き先候補の EVA の電力レートを仮計算する．
        v_list = []
        for eva_id, eva_dis in ev._EVA_can.items():
            eva = self._EVA_list[eva_id]        
            eva.add_EV(ev)
            P_rate = eva.get_P_rate(ev) 
        
            # 多項ロジットモデル
            v_cal = ev._kappa_dis*eva_dis + ev._kappa_P*P_rate
            v_list.append(v_cal)
            eva.remove_EV(ev)                   
        
        # Gumbel distribution
        all_v = 0
        for i in v_list:
            all_v += math.exp(-ev._kappa_nu*i)                           

        # random.choices を使用するため，リストに変換
        pr = [math.exp(-ev._kappa_nu*j) / all_v for j in v_list]
        EVA_can_list = [EVA_id for EVA_id in ev._EVA_can]

        
        # 各 EVA の効用をもとにランダムに一つの EVA を選択し，追加する
        select_EVA_id = random.choices(EVA_can_list, k = 1, weights = pr)
        ev._EVA_id = select_EVA_id[0]
        self._EVA_list[ev._EVA_id].add_EV(ev)

    
    def get_next_dep_EV(self) -> object:
        # 次に出発する EV を選択
        next_dep_ev = EV(id = 0)  # ダミー ev の作成
        next_dep_ev.set_param_time(arrT = 0, depT = 1000, nowT = 0)
        next_depT = 1000
        for eva in self._EVA_list:     
            for ev in eva._EV_list.values():
                print(ev._depT, ev._preT)
                if ev._depT < ev._preT:
                    depT = ev._depT
                else:
                    depT = ev._preT
                    
                if depT < next_depT:
                    next_dep_ev = ev
                    next_depT = depT
        
        return next_dep_ev, next_depT
    
            
    def read_data_from_file(self, file) -> None:  # ファイルの読み込み
        for line in open(file, "r"):
            EVA_data_tmp = {}
            data = list(map(int, line.split()))

            j = int(len(data)/2)
            for i in range(j):
                EVA_data_tmp.update({data[i]: data[j + i]})
            self._EVA_candidate_list.append(EVA_data_tmp)


    def EVA_candidate_generator(self):
        for EVA_candidate in self._EVA_candidate_list: 
            yield EVA_candidate


    def simulation(self):
        EV_id = 0
        t = self._stT                 # current time
        next_arrT = self.rnd_exp()    # next arrive time
        next_depT = self._endT        # next departure time

        while (t < self._endT):
            if (next_arrT < next_depT):
                # 到着時刻 t までの電力売買を完了させる．
                t = next_arrT
                self.calc_all_EVA(t)

                # EV を生成し，売買する EVA を選択
                ev = make_EV(id = EV_id + 1, arrT = t, depT = t + self.rnd_exp() + 0.5,
                             k_dis = 0.03, k_P = kappa_P, k_nu = kappa_nu)
                self.select_EVA_and_add_EV(ev)                      
                EV_id += 1

                # 次に到着する EV の時刻を格納
                next_arrT += self.rnd_exp()

            else:
                # 出発時刻 t までの電力売買を完了させる．
                t = next_depT            
                self.calc_all_EVA(t)

                # 出発する EV の処理                    
                self.process_dep_EV(next_dep_EV)   

            self.calc_all_EVA(t)
            # 次に出発する (EV, EV の時刻) を格納          
            next_dep_EV, next_depT = self.get_next_dep_EV()      
             



    def check_simulation(self):
        EV_id = 0
        t = self._stT                 # current time
        next_arrT = self.rnd_exp()    # next arrive time
        next_depT = self._endT        # next departure time

        while (t < self._endT):
            if (next_arrT < next_depT):
                # 到着時刻 t までの電力売買を完了させる．
                t = next_arrT
                self.calc_all_EVA(t)

                # EV を生成し，売買する EVA を選択
                ev = make_EV(id = EV_id + 1, arrT = t, depT = t + self.rnd_exp() + 0.5,
                             k_dis = 0.03, k_P = kappa_P, k_nu = kappa_nu)
                self.select_EVA_and_add_EV(ev)                      
                EV_id += 1
                
                print("EV_kind: {0} Event arrT: {1} ".format(ev._kind, t))
                self.print_EV_num()            
                
                # 次に到着する EV の時刻を格納
                next_arrT += self.rnd_exp()                
          
            else:
                # 出発時刻 t までの電力売買を完了させる．
                t = next_depT            
                self.calc_all_EVA(t)
                print("Event depT: {0}".format(t))
                
                # 出発する EV の処理                    
                self.process_dep_EV(next_dep_EV)
                self.print_EV_num()


            self.calc_all_EVA(t)

            # 次に出発する EV の時刻を格納          
            next_dep_EV, next_depT = self.get_next_dep_EV()      
            self.print_next_event_time(next_arrT, next_depT)
            self.print_EV_price_rate()

            
    def print_dep_list(self) -> None:
        print("dep_EV_list")
        for ev in self._dep_ev_list:
            print("id: {1} kind: {2} EVA: {0} arrT: {3} depT: {4} totalT: {5} energyT: {6} priceT: {7}"
                  .format(ev._EVA_id, ev._id, ev._kind, ev._arrT, ev._depT,
                          ev._depT - ev._arrT, round(ev._total_E_kWh, 3),
                          round(ev._total_P_yen, 3)))

    def print_EV_price_rate(self) -> None:
        for eva in self._EVA_list:
            for ev in eva._EV_list.values():
                if ev._id != 0:
                    print("EVA: {0} kind: {1} id: {2} E_rate: {3} E_now: {4} P_rate: {5} P_now: {6}"
                          .format(eva._id, ev._kind, ev._id, round(ev._E_rate_kW, 2),
                                  round(ev._total_E_kWh, 2), round(ev._P_rate, 3),
                                  round(ev._total_P_yen, 3)))            
        print()

    def print_EV_num(self):
        for eva in self._EVA_list:
            print("EVA: {0} S_num: {1} Bnum: {2} Battry_kWh: {3}"
                  .format(eva._id, eva._S_EV_num, eva._B_EV_num, eva._battery_kWh))
            
    def print_next_event_time(self, next_arr_time, next_dep_time):
        print("next_arr_time: {0} next_dep_time: {1}".format(next_arr_time, next_dep_time))

        
            
        
def calc_norm(vec) :
    """
      calculate the 2nd norm of vector
    """
    norm = 0.0
    for v in vec:
        norm += v*v
        
    return math.sqrt(norm)


def make_EV(id, arrT, depT, k_dis, k_P, k_nu):
    ev = EV(id = id)
    ev.set_param_time(arrT = arrT, depT = depT, nowT = arrT)
    ev.set_param_model(kappa_dis = k_dis, kappa_P = k_P, kappa_nu = k_nu)
    ev.set_param_calc(alpha = 2, base_P = 17)

    # EV の行き先候補をセット
    EVA_candidate = sim.EVA_candidate_generator()
    EVA_can = EVA_candidate.__next__()
    ev.set_EVA_candidate(EVA_can)
        
    return ev



    
if __name__ == "__main__":
    # parameter setting for simulation
    seed = int(sys.argv[1])
    EVA_num = int(sys.argv[2])         
    kappa_P = float(sys.argv[3])       # 多項ロジットモデルでの価格の重み
    kappa_nu = float(sys.argv[4])      # 多項ロジットモデルでのランダム性の強さ
    candidate_file = sys.argv[5]       # EV の行き先候補が書き込まれているファイル
    
    # make simulator
    stT = 0         
    endT = 6        
    sim = Simulator(stT = stT, endT = endT)

    # make EVA
    for i in range(EVA_num):
        eva = EVA(id = i)
        eva.set_param(limit_As = 64, limit_Ar = 64) 
        sim.add_EVA(eva)

    # preparation for simulation 
    sim.read_data_from_file(candidate_file)
    random.seed(seed)

    #sim.simulation()
    sim.check_simulation()
    sim.print_dep_list()
    
    
