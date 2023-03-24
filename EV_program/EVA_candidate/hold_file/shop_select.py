import pandas as pd
import random


def read_csv(file):
    filename = file   #読み込むファイル
    data = pd.read_csv(filename, header=None)   #データの読み込み

    return data

    
def population(line,sum):
    p=[]
    for fi in line:   #人口分布
        p.append(fi/sum)
        
    return p


def main():
    data = read_csv( "data_1.csv" )
    print(data)
    lst = [i for i in range(len(data))]
    s = sum (data[1])
    p = population(data[1], s)
    choice_house = random.choices(lst, k=100, weights=p)    #確率に従って抽出

    for num in choice_house:
        print(data[2][num])


if __name__ ==  "__main__":
    main()
    
    
