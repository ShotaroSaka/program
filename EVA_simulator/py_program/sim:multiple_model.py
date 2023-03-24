#!/usr/bin/env python3
import math
import numpy as np

def calc_pro(W_1, W_2, W_3, W_4):
    lamda = 0.4   # 選択のランダム性
    pr_1 = math.exp(lamda*W_1) / (math.exp(lamda*W_1) + math.exp(lamda*W_2))
    pr_2 = math.exp(lamda*W_3) / (math.exp(lamda*W_3) + math.exp(lamda*W_4))
    print(pr_1, 1 - pr_1, pr_2, 1 - pr_2)



alpha = -0.03   # 距離に対する重み
beta = 0       # 価格に対する重み(価格提示なし)
beta_c = -5    # 価格に対する重み(価格提示あり)


d_1 = 250       # EVA_1 距離
d_2 = 300       # EVA_2 距離
p_2 = 13       # EVA_2 価格

for p_1 in np.arange(12.5, 15.5, 0.2):
    W_1 = alpha*d_1 + beta_c*p_1
    W_2 = alpha*d_2 + beta_c*p_2
    W_3 = alpha*d_1 + beta*p_1
    W_4 = alpha*d_2 + beta*p_2
    
    print(str(p_1)+" ",end="")
    calc_pro(W_1, W_2, W_3, W_4)
    
    
    
