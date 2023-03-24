import sys
import math
import numpy as np
from scipy.integrate import odeint
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import random

class EV(object) :
    def __init__(self, id, kind) :
        self._id = id         # identification number of the EV group
        self._kind = kind     # kind of EVs (kind = 'S' or kind = 'B') in the group
        self._kappa_s = 1000 #売電価格の計算式における係数
        self._kappa_b = 1000 #買電価格の計算式における係数


    def set_time(self, arrT, depT, t_a) :
        self._arrT = arrT         # arrival time of EV
        self._depT = depT         # departure time of EV
        self._t_a = t_a

    def set_quantity(self):
      x = int(random.random() * 50 + 75) #Es,Ebともに，75~125の範囲でランダム性をもたせた．
      return x
    

    def set_param(self, gamma, kappa_r, base_p, Es, Eb) :
        self._gamma = gamma    # parameter of the utility function
        self._kappa_r = kappa_r          # coefficient used in the derivs kappa_rs,rbの部分，実際には0.1で計算を行っている
        self._base_p = base_p  # base line of price
        self._Es = Es
        self._Eb = Eb
        self._E_now = 0
        self._rate = 1
        self._gamma_fact = 2
        self._finish_rate = 1

        if self._kind == 'S' : 
          self._price = self._Es*self._base_p
          self._price_pre = self._Es*self._base_p
          self._price_rate = self._base_p
        else:
          self._price = self._Eb*self._base_p
          self._price_pre = self._Eb*self._base_p
          self._price_rate = self._base_p


    def derivs_util(self, x) :
        return (x+1)**(-self._gamma)   # differential equation of the utility function

    def derivs_x(self, x, p) :
        return self._kappa_r*(self.derivs_util(x) - p*x)  # ここのｘがわからない differential equation of the rate

    def calc_p(self, rate, p, t1) : #現状態での価格であって，売買終了まで，売りては価格が下がり続け，買い手は価格が上がり続ける．プリントしても意味がない#現状態で電力売買を続けたときの最終的な価格を仮で表示したい．t1をendT,t_aは現在の時間で計算すればできそうね！
        if self._kind == 'S' :    # for sellers
          
          self._price -= self._kappa_s*rate**(self._gamma_fact)*(p[0] - p[2])*(t1 - self._t_a)
          self._price_pre = self._price - (self._kappa_s*rate**(self._gamma_fact)*(p[0] - p[2])*(self._depT - t1))
          #self._price_rate = self._price_pre / self._Es
          #print("rate{0}, base_p{1}, kappas{2}, qs {3}, -qm {4}".format(rate,self._base_p,self._kappa_s, p[0], p[2]))
          self._price_rate = rate*self._base_p - self._kappa_s*rate**(self._gamma_fact)*(p[0] - p[2])# 先生
          
        else:
          
          self._price += self._kappa_b*rate**(self._gamma_fact)*(p[1] + p[2])*(t1 - self._t_a)
          self._price_pre = self._price + (self._kappa_b*rate**(self._gamma_fact)*(p[1] + p[2])*(self._depT - t1)) 
          #self._price_rate = self._price_pre / self._Eb
          #print("rate{0}, base_p{1}, kappab{2}, qb {3}, +qm {4}".format(rate,self._base_p,self._kappa_b, p[1], p[2]))
          self._price_rate = rate*self._base_p + self._kappa_b*rate**(self._gamma_fact)*(p[1] + p[2]) # 先生


    def calc_E_now(self, rate, t1):
      self._E_now += rate * (t1 - self._t_a)
      #print("id: {0} kind: {1} arrT: {2} depT: {3} totalT: {4} price: {7} price_pre: {5} E_now{6} price_rate:{8}".format(self._id,self._kind,self._arrT, self._depT,self._depT - self._arrT, self._price_pre, self._E_now, self._price, self._price_rate))

class EVA(object) :
    def __init__(self, id ) :
        self._id = id
        self._EV_list = {}

    def set_param(self, k1, k2, k3, limit_As, limit_Ar,dis, rs, rb) :
        self._k1 = k1
        self._k2 = k2
        self._k3 = k3
        self._limit_As = limit_As
        self._limit_Ar = limit_Ar
        self._dis = dis
        self._rs = rs
        self._rb = rb
        self._s_num = 1
        self._b_num = 1

        self._kappa_dis = 1
        #self._kappa_dis = 0
        #self._kappa_rate_s = 0.0075
        #self._kappa_rate_b = -0.0075
        self._kappa_rate_s = 0.1
        self._kappa_rate_b = -0.1

        #self._kappa_rate_s = 0
        #self._kappa_rate_b = 0

        #self._kappa_rate = 0
        self._lamda = 1


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

    def calc_depT(self, rate):
      for ev in self._EV_list.values():
        if ev._kind == "S":
          ev._depT = ev._t_a + (ev._Es - ev._E_now) / rate
        else:
          ev._depT = ev._t_a + (ev._Eb - ev._E_now) / rate
        


    def set_init(self, init_x, init_p):
      self._init = [init_x]*len(self._EV_list) + [init_p]*3


    
    def get_conv(self, e_time) :
      self._opt = minimize(self.norm_derivs, self._init)#その時のレートとペナを計算する

      EV_n = len(self._EV_list)
      x = {}

      p1 = self._opt.x[EV_n]
      p2 = self._opt.x[EV_n+1]
      p3 = self._opt.x[EV_n+2]
      i = 0
      for ev in self._EV_list.values() :
          x[i] = self._opt.x[i]  # レート of EV id

          ev._rate = x[i]

          ev.calc_p(x[i], (p1, p2, p3),e_time) #価格を更新する（etimeまでの合計価格）

          ev.calc_E_now(x[i], e_time) #etimeまでの総充電量

          ev._t_a = e_time #今の時間を保存する

          self.calc_depT(x[i]) #レートとenowが更新されたので，depTを計算する

          i += 1

      #print(x[i])

    def derivs(self, t, y) :
      """
          calculate
      """
      ## calculate the both aggregate rates of sellers and buyers.
      As = Ar = 0.0
      i = 0
      
      for ev in self._EV_list.values():
        if ev._kind == "S":
          As += y[i]
        else:
          Ar += y[i] 
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


class Simulator(object) :
    def __init__(self, stT, endT) :
        self._stT = stT    # start time of simulation
        self._endT = endT  # end time of simulation

        self._print_EV_list = []  # print list of EVs
        self._EVA_list = [] #複数のときはこっち

        self._pr = []
        self._v_list = []

        self._EVA_id = 0

        self._sol = None   # time series of states
        self._opt = None   # convergence values of states

    def add_print_EV_list(self, id) :
        self._print_EV_list.append(0)
        self._print_EV_list.append(id)

    def add_EVA(self, EVA) :
        #self._EVA = EVA #単数のとき
        self._EVA_list.append(EVA) #複数のとき


    def evol(self, init) :
        """
        obtain the time series of states using Scipy's funcition 'solve_ivp'
        """
        self._sol = solve_ivp(self.derivs, (self._stT, self._endT), init, dense_output = True, method='Radau')

    def print_time_series(self) :
        assert self._sol != None

        EV_n = len(self._EV_list)
        for i in range(len(self._sol.t)) :
            print("TIME: t {0} ".format(self._sol.t[i]), end="")

            x = {}
            for id in self._print_EV_list :
                x[id] = self._sol.y[id, i]
                print("x{0} {1} ".format(id, x[id]), end="")

            p1 = self._sol.y[EV_n, i]
            p2 = self._sol.y[EV_n+1, i]
            p3 = self._sol.y[EV_n+2, i]
            print("p1 {0} p2 {1} p3 {2} ".format(p1, p2, p3), end="")

            for id in self._print_EV_list :
                px = self._EVA_list[0]._EV_list[id].calc_p(x[id], (p1, p2, p3))
                print("px{0} {1} ".format(id, px), end="")

            print()



    def print_conv(self) :
      for eva in self._EVA_list:
        
        assert eva._opt != None

        EV_n = len(eva._EV_list)

        print("EVA: {0} ".format(eva._id), end="")
        #print("EVA: ", eva._id, end="")

        print("OPT: opt {0} ".format(eva._opt.fun), end="")

        x = {}
        for ev in eva._EV_list :
            x[ev._id] = eva._opt.x[ev._id]  # rate of EV id
            print("x{0} {1} ".format(ev._id, x[ev._id]), end="")

        p1 = eva._opt.x[EV_n]
        p2 = eva._opt.x[EV_n+1]
        p3 = eva._opt.x[EV_n+2]
        print("p1 {0} p2 {1} p3 {2} ".format(p1, p2, p3), end="")

        for ev in eva._EV_list :
            px = ev.calc_p(x[ev._id], (p1, p2, p3))
            print("px{0} {1} ".format(ev._id, px), end="")

        print()


    def EVA_choise(self):
      r = random.random()
      sum = self._pr[0]
      for i in range(len(self._pr)):
        if sum >= r:
          self._EVA_id = i
          print("選択したEVA = {0}".format(self._EVA_id))
          break
        else:
          sum += self._pr[i+1]

    def EVA_choise_EVA1(self):
      self._EVA_id = 0


def calc_norm(vec) :
    """
      calculate the 2nd norm of vector
    """
    norm = 0.0
    for v in vec:
        norm += v*v

    return math.sqrt(norm)

#以下メイン文
def rnd_exp(lam):
  u = random.random()
  x = (-1 / lam)*math.log(1-u)
  return x

def make_EVA(EVA_num):
  #  eva = EVA(id = 0)
  #  eva.set_param(k1 = 0.1, k2 = 0.1, k3 = 0.1, limit_As = 64, limit_Ar = 64, dis = 3.5 , rs = 1, rb = 1)
  #  sim.add_EVA(eva)

  # eva = EVA(id = 1)
  # eva.set_param(k1 = 0.1, k2 = 0.1, k3 = 0.1, limit_As = 64, limit_Ar = 64, dis = 5, rs = 1, rb = 1)
  # sim.add_EVA(eva)

  # eva = EVA(id = 2)
  # eva.set_param(k1 = 0.1, k2 = 0.1, k3 = 0.1, limit_As = 64, limit_Ar = 64, dis = 6, rs = 1, rb = 1)
  # sim.add_EVA(eva)
    for i in range(EVA_num):
        eva = EVA(id = i)
        eva.set_param(k1 = 0.1, k2 = 0.1, k3 = 0.1, limit_As = 64, limit_Ar = 64, dis = random.uniform(2,5), rs = 1, rb = 1)
        sim.add_EVA(eva)

def make_first_EV(EVA_num,EV_num):
  for i in range(EVA_num):
    for j in range(EV_num):
      if j%2 == 0:
        seller = EV(id = j, kind = 'S')
        seller.set_time(arrT = stT, depT = endT, t_a = stT)
        seller.set_param(gamma = alpha, kappa_r = 0.1, base_p = 15, Es = 10000, Eb = 0)
        seller._price_rate = 50
        sim._EVA_list[i].add_EV(seller)
      else:
        buyer = EV(id = j, kind = 'B')
        buyer.set_time(arrT = stT, depT = endT, t_a = stT)
        buyer.set_param(gamma = beta, kappa_r = 0.1, base_p = 16, Es = 0, Eb = 10000)
        buyer._price_rate = 25
        sim._EVA_list[i].add_EV(buyer)

def set_init(EVA_num):
  for i in range(EVA_num):
    sim._EVA_list[i].set_init(init_x, init_p)

def print_EV_in_EVA(sim):
  for eva in sim._EVA_list:
    for ev in eva._EV_list.values():
      print("EVA{6} id {5} kind {0}, Es{1}, Eb {2}, arrT {3}, depT {4}".format(ev._kind,ev._Es,ev._Eb,ev._arrT,ev._depT, ev._id , eva._id))

def make_EV(i, sim, kind):
  #if random.random() >= 0.5:
  if kind == "S":
    seller = EV(id = i, kind = 'S')
    seller.set_time(arrT = t, depT = t + 50 , t_a = t)
    #seller.set_param(gamma = 1.5 + random.uniform(0.25,0.75), kappa_r = 0.1, base_p = 5, Es = seller.set_quantity(), Eb = 0)
    #seller.set_param(gamma = alpha, kappa_r = 0.1, base_p = 5, Es = seller.set_quantity(), Eb = 0)
    #seller.set_param(gamma = alpha , kappa_r = 0.1, base_p = 5, Es = 100, Eb = 0)
    seller.set_param(gamma = alpha , kappa_r = 0.1, base_p = 15, Es = 17, Eb = 0)
    #seller.set_param(gamma = int(random.random() * 3) + 1 , kappa_r = 0.1, base_p = 5, Es = 100, Eb = 0)
    #seller.set_param(gamma = 10 , kappa_r = 0.1, base_p = 5, Es = 100, Eb = 0)
    #到着処理
    sim._EVA_list[sim._EVA_id].add_EV(seller)
    sim._EVA_list[sim._EVA_id]._s_num += 1
  else:
    buyer = EV(id = i, kind = 'B')
    buyer.set_time(arrT = t, depT = t + 50, t_a = t)
    #buyer.set_param(gamma = 1.5 + random.uniform(0.25,0.75), kappa_r= 0.1, base_p = 5, Es = 0, Eb = buyer.set_quantity())
    #buyer.set_param(gamma = beta, kappa_r= 0.1, base_p = 5, Es = 0, Eb = buyer.set_quantity())
    #buyer.set_param(gamma = beta, kappa_r= 0.1, base_p = 5, Es = 0, Eb = 100)
    buyer.set_param(gamma = beta, kappa_r= 0.1, base_p = 17, Es = 0, Eb = 100)
    #buyer.set_param(gamma = int(random.random() * 3) + 1, kappa_r= 0.1, base_p = 5, Es = 0, Eb = 100)
    #到着処理
    sim._EVA_list[sim._EVA_id].add_EV(buyer)
    sim._EVA_list[sim._EVA_id]._b_num += 1

"""
def set_ev_min(ev_min):    
  ev_min = EV(id = 0, kind = 'S')
  ev_min._depT = endT*10
  return ev_min
"""

def print_next_event_time():
  print("next_arr_time: {0} next_dep_time: {1}".format(next_arr_time,next_dep_time))

def print_del_ev(ev_min):
  print("del ev id: {0} kind: {1} arrT: {2} depT: {3} totalT: {4} price: {5}".format(ev_min._id,ev_min._kind,ev_min._arrT, ev_min._depT,ev_min._depT - ev_min._arrT, ev_min._price))

def calc_all(sim, t):
  for eva in sim._EVA_list:
    eva.set_init(init_x, init_p)
    eva.get_conv(t)
  
  
    
def print_dep_list():
  print("dep_EV_list")
  for i in range(EVA_num):
    for ev in dep_ev_list[i]:
      print(" EVA {7} id: {0} kind: {1} gamma:{6} arrT: {2}  depT: {3} totalT: {4} price: {5}".format(ev._id,ev._kind,ev._arrT, ev._depT,ev._depT - ev._arrT, ev._price, ev._gamma,i))
  # for ev in dep_ev_list_1:
  #   print(" EVA 0 id: {0} kind: {1} gamma:{6} arrT: {2}  depT: {3} totalT: {4} price: {5}".format(ev._id,ev._kind,ev._arrT, ev._depT,ev._depT - ev._arrT, ev._price, ev._gamma))

  # print("")  
  # for ev in dep_ev_list_2:
  #   print("EVA 1 id: {0} kind: {1} gamma:{6} arrT: {2} depT: {3} totalT: {4} price: {5}".format(ev._id,ev._kind,ev._arrT, ev._depT,ev._depT - ev._arrT, ev._price, ev._gamma))

  # print("")  
  # for ev in dep_ev_list_3:
  #   print("EVA 2 id: {0} kind: {1} gamma:{6} arrT: {2} depT: {3} totalT: {4} price: {5}".format(ev._id,ev._kind,ev._arrT, ev._depT,ev._depT - ev._arrT, ev._price, ev._gamma))

#  print("dep list")
#  for ev in dep_ev_list:
#    print("id: {0} kind: {1} gamma:{7} arrT: {2} depT: {3} totalT: {4} price: {5} finish_price_rate:{6}".format(ev._id,ev._kind,ev._arrT, ev._depT,ev._depT - ev._arrT, ev._price, ev._finish_rate, ev._gamma))
'''
def print_EV_rate(sim,EVA_id):
  for ev in sim._EVA_list[EVA_id]._EV_list.values():
    if ev._kind == "S":
      print("kind: {0} , id: {1} , gamma:{2} , rate: {3}".format(ev._kind, ev._id, ev._gamma , ev._rate))

  for ev in sim._EVA_list[EVA_id]._EV_list.values():
    if ev._kind == "B":
      print("kind: {0} , id: {1} , gamma:{2} , rate: {3}".format(ev._kind, ev._id, ev._gamma, ev._rate))
  print()

'''
#print_EV_rate の案
def print_EV_rate(sim):
  for eva in sim._EVA_list:
    for ev in eva._EV_list.values():
      if ev._kind == "S":
        print("EVA{3} , kind: {0} , id: {1} , rate: {2}".format(ev._kind, ev._id, ev._rate, eva._id))

    for ev in eva._EV_list.values():
      if ev._kind == "B":
        print("EVA:{3}, kind: {0} , id: {1} , rate: {2}".format(ev._kind, ev._id, ev._rate, eva._id))
  print()

def print_EV_num(sim):
  for eva in sim._EVA_list:
    print("EVA {0}, S_num = {1}, Bnum = {2}".format(eva._id, eva._s_num, eva._b_num))

def print_EV_price_rate(sim):
  for eva in sim._EVA_list:
    for ev in eva._EV_list.values():
      print("EVA{0} , kind: {1} , id: {2} , rate: {3}, E_now:{4}, price:{5}, price_pre:{6}, price_rate:{7}".format(eva._id, ev._kind, ev._id, ev._rate, ev._E_now, ev._price, ev._price_pre, ev._price_rate))




def calc_pro(v_list,lamda,sim):
      zentai = 0
      for i in v_list:
        zentai += math.exp(lamda*i)
    
      sim._pr = [math.exp(lamda*j) / zentai for j in v_list]

# vを設定する
def calc_v(sim,kind):
  v_cal = 0
  sim._v_list = []
  for eva in sim._EVA_list: 
    if kind == "B":
      v_cal = -eva._kappa_dis * eva._dis - eva._kappa_rate_b * eva._EV_list[1]._price_rate
      #print("kind {5} ,kappa_dis {0}, dis {1}, kappa_rate{2}, price_rate{3} , v{4}".format(eva._kappa_dis, eva._dis, eva._kappa_rate_b, eva._EV_list[1]._price_rate, v_cal, kind))
      sim._v_list.append(v_cal)
    else:
      v_cal = -eva._kappa_dis * eva._dis + eva._kappa_rate_s * eva._EV_list[0]._price_rate
      #print("kind {5}, kappa_dis {0}, dis {1}, kappa_rate{2}, price_rate{3} , v{4}".format(eva._kappa_dis, eva._dis, eva._kappa_rate_s, eva._EV_list[0]._price_rate, v_cal, kind))
      sim._v_list.append(v_cal)

      #random.seed(1)
random.seed(2)

#EVの発生頻度の調節のためのlam(大きければ大きいほど発生頻度が上がる)
lam = 5

#EV選択確率のランダム性を表すlamda(1 だとばらつきなし，０に近づくほどランダム性増加)
#lamda = 1
#lamda = 0.5
#lamda = 0.25
lamda = 0.1
## parameter setting for ev # parameter of the utility function for buyers
alpha = 2
beta = 2                   

## make simulator
stT = 0
endT = 6
sim = Simulator(stT = stT, endT = endT)

## make EV aggregater （複数）
EVA_num = 3
make_EVA(EVA_num)

#売り手と買い手は1台ずつ生成しておく(EVA_num)
EV_num = 2
make_first_EV(EVA_num,EV_num)

#set_initの初期
init_x = 1.0        # initial rates of EVs
init_p = 0.0        # initial price→pena
set_init(EVA_num)

#存在するEVAと，その中に現在いるEVを出力する(EVAへのEVの初期配置確認)
#print_EV_in_EVA(sim)

#出発到着時間の初期化
next_arr_time = rnd_exp(lam)
next_dep_time = endT
i = EV_num
t = 0

dep_ev_list = []
for i in range(EVA_num):
  dep_ev_list.append([])
    

while(t < endT):
  if(next_arr_time < next_dep_time):
    t = next_arr_time
    print("Event arrT :{0}".format(t))

#この部分でEVA選択を行う
    if random.random() >= 0.5:
      kind = "S"
    else:
      kind = "B"

    calc_v(sim,kind)

    #print("v_list")
    #print(sim._v_list)
    
    calc_pro(sim._v_list, lamda, sim)
    print("pr(選択確率)")
    print(sim._pr)


    #sim._EVA_id = sim.EVA_choise() ここがわるさしてそう

    #make EV
    sim.EVA_choise() #EVAidをせんたくするものにした．
    #sim.EVA_choise_EVA1() #EVAidを０にした（テスト用）

    #print(sim._EVA_id) #ここが何故かnoneになってしまう．ニコ上消したらできた

    make_EV(i, sim, kind)
    i += 1

    print_EV_num(sim) #今現在のEVAの中にいるEVの台数の出力

    calc_all(sim, t)

    ev_min = EV(id = 0, kind = 'S')
    ev_min._depT = endT*10

    for eva in sim._EVA_list:
      for ev in eva._EV_list.values():
        if ev._depT < ev_min._depT:
          ev_min = ev
          sim._EVA_id = eva._id
    ##print("evmin の EVA_id = {0} , ev_id{1} ".format(sim._EVA_id, ev_min._id))
        
    next_dep_time = ev_min._depT #next_dep_timeの更新
    
    next_arr_time += rnd_exp(lam) #next_arr_timeの更新
    
    print_next_event_time()

    


  else:    #EVの離脱処理を行う．
    t = next_dep_time
    print("Event depT : {0}".format(t))

    calc_all(sim, t)

    print_del_ev(ev_min) #リストから削除するevを出力
  
  #EVAの台数を増やす場合はいかに追加
    
    dep_ev_list[sim._EVA_id].append(sim._EVA_list[sim._EVA_id]._EV_list[ev_min._id]) #削除するEVを完了リストに追加
    if sim._EVA_list[sim._EVA_id]._EV_list[ev_min._id]._kind == "S":
      sim._EVA_list[sim._EVA_id]._s_num -= 1
    else:
      sim._EVA_list[sim._EVA_id]._b_num -= 1

    # elif sim._EVA_id == 1:
    #   dep_ev_list_2.append(sim._EVA_list[sim._EVA_id]._EV_list[ev_min._id]) #削除するEVを完了リストに追加
    #   if sim._EVA_list[sim._EVA_id]._EV_list[ev_min._id]._kind == "S":
    #     sim._EVA_list[sim._EVA_id]._s_num -= 1
    #   else:
    #     sim._EVA_list[sim._EVA_id]._b_num -= 1

    # elif sim._EVA_id == 2:
    #   dep_ev_list_3.append(sim._EVA_list[sim._EVA_id]._EV_list[ev_min._id]) #削除するEVを完了リストに追加
    #   if sim._EVA_list[sim._EVA_id]._EV_list[ev_min._id]._kind == "S":
    #     sim._EVA_list[sim._EVA_id]._s_num -= 1
    #   else:
    #     sim._EVA_list[sim._EVA_id]._b_num -= 1

    #dep_ev_list.append(sim._EVA_list[EVA_id]._EV_list[ev_min._id]) #削除するEVを完了リストに追加

    del sim._EVA_list[sim._EVA_id]._EV_list[ev_min._id] #リストから削除する
    
    calc_all(sim, t)

    
    #稼働中のEVの中で離脱時間の最小値＝next_dep_timeに設定
    ev_min = EV(id = 0, kind = 'S')
    ev_min._depT = endT*10
    for eva in sim._EVA_list:
      for ev in eva._EV_list.values():
        if ev._depT < ev_min._depT:
          ev_min = ev
          sim._EVA_id = eva._id


    next_dep_time = ev_min._depT    

    print_next_event_time()

    print_EV_num(sim)

  #print_EV_rate(sim,EVA_id) #基本的に ９/台数 担っていることを確認済み，積極性を変えるとそれに伴ってレートも変化することも確認済み
  #print_EV_rate(sim)
  print_EV_price_rate(sim)
  print()

print_dep_list()
