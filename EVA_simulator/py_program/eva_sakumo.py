import sys
import math
import numpy as np
from scipy.integrate import odeint
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

class EV(object) :
    def __init__(self, id, kind) :
        self._id = id         # identification number of the EV group
        self._kind = kind     # kind of EVs (kind = 'S' or kind = 'B') in the group
        
    def set_time(self, arrT, depT) :
        self._arrT = arrT         # arrival time of EV
        self._depT = depT         # departure time of EV

    def set_param(self, gamma, ki, base_p) :
        self._gamma = gamma    # parameter of the utility function
        self._ki = ki          # coefficient used in the derivs
        self._base_p = base_p  # base line of price


    def derivs_util(self, x) :
        return (x+1)**(-self._gamma)   # differential equation of the utility function

    def derivs_x(self, x, p) :
        return self._ki*(self.derivs_util(x) - p*x)  # differential equation of the rate
    
    def calc_p(self, x, p) :
        if self._kind == 'S' :    # for sellers
            return self._base_p - x*(p[0] - p[2])
        elif self._kind == 'B' :  # for buyers
            return self._base_p + x*(p[1] + p[2])

        
class EVA(object) :
    def __init__(self, id) :
        self._id = id
        
    def set_param(self, k1, k2, k3, limit_As, limit_Ar) :
        self._k1 = k1
        self._k2 = k2
        self._k3 = k3
        self._limit_As = limit_As
        self._limit_Ar = limit_Ar
        
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


class Simulator(object) :
    def __init__(self, stT, endT) :
        self._stT = stT    # start time of simulation
        self._endT = endT  # end time of simulation

        self._EV_list = []
        self._print_EV_list = []  # print list of EVs
        self._EVA = None
        
        self._sol = None   # time series of states
        self._opt = None   # convergence values of states

        
    def add_EV(self, EV) :
        self._EV_list.append(EV)

    def add_print_EV_list(self, id) :
        self._print_EV_list.append(id)
        
    def add_EVA(self, EVA) :
        self._EVA = EVA

    def derivs(self, t, y) :
        """
           calculate
        """ 
        ## calculate the both aggregate rates of sellers and buyers.
        As = Ar = 0.0
        i = 0
        for ev in self._EV_list:
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

        for ev in self._EV_list :
            x = y[i]
            if ev._kind == 'S' :    p = p1 - p3
            elif ev._kind == 'B' :  p = p2 + p3
            else :                assert(False)

            dy.append(ev.derivs_x(x, p))
            i += 1
        dy = dy + self._EVA.derivs_p(As, Ar, p1, p2, p3)


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
        print(dy)
        return calc_norm(dy)/calc_norm(y)

    
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
                px = self._EV_list[id].calc_p(x[id], (p1, p2, p3))
                print("px{0} {1} ".format(id, px), end="")
                
            print()

            
    def get_conv(self, init) :
        self._opt = minimize(self.norm_derivs, init)

    def print_conv(self) :
        assert self._opt != None

        EV_n = len(self._EV_list)

        print("OPT: opt {0} ".format(self._opt.fun), end="")
            
        x = {}
        for id in self._print_EV_list :
            x[id] = self._opt.x[id]  # rate of EV id
            print("x{0} {1} ".format(id, x[id]), end="")

        p1 = self._opt.x[EV_n]
        p2 = self._opt.x[EV_n+1]
        p3 = self._opt.x[EV_n+2]
        print("p1 {0} p2 {1} p3 {2} ".format(p1, p2, p3), end="")

        for id in self._print_EV_list :
            px = self._EV_list[id].calc_p(x[id], (p1, p2, p3))
            print("px{0} {1} ".format(id, px), end="")
            
        print()

        
def calc_norm(vec) :
    """
      calculate the 2nd norm of vector
    """
    norm = 0.0
    for v in vec:
        norm += v*v
        
    return math.sqrt(norm)



def main() :
    ## parameter setting for sellers
    ns = int(sys.argv[1])       # number of sellers
    alpha = float(sys.argv[3])  # parameter of the utility function for sellers

    ## parameter seeting for EVs of buyers
    nr = int(sys.argv[2])      # number of buyers
    beta = float(sys.argv[4])  # parameter of the utility function for sellers

    ## make simulator
    stT = 0
    endT = 10000
    sim = Simulator(stT = stT, endT = endT)
    
    ## make EV aggregater
    eva = EVA(id = 1)
    eva.set_param(k1 = 0.1, k2 = 0.1, k3 = 0.1, limit_As = 9, limit_Ar = 9)
    sim.add_EVA(eva)

    init = []           # initial state of states
    init_x = 1.0        # initial rates of EVs
    init_p = 0.0        # initial prices
    
    ## make  sellers
    for i in range(ns) :
        seller = EV(id = i + 1, kind = 'S')
        seller.set_time(arrT = stT, depT = endT)
        seller.set_param(gamma = alpha, ki = 0.1, base_p = 10)
        sim.add_EV(seller)

        init.append(init_x)  # set initial state of the rates of EVs
        
    ## make buyers
    for i in range(nr) :
        buyer = EV(id = i + 1 + ns, kind = 'B')
        buyer.set_time(arrT = stT, depT = endT)
        buyer.set_param(gamma = beta, ki = 0.1, base_p = 10)
        sim.add_EV(buyer)

        init.append(init_x)  # set initial state of the rates of EVs

    init = init + [init_p]*3 # set initial prices

    ## setting of the EV output
    sim.add_print_EV_list(0)     # add the print list of the first seller 
    sim.add_print_EV_list(ns)    # add the print list of the first buyer


    ## calculate the time series of states
  #  print(init)
    #sim.evol(init)
    #sim.print_time_series()


    ## calculate the convergenced states
    sim.get_conv(init)
    sim.print_conv()
    
if __name__ == '__main__' :
    main()

