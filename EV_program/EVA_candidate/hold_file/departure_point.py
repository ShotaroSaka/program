import pandas as pd
import random
import csv

def read_csv(file):
    filename = file   #読み込むファイル
    data = pd.read_csv(filename, header=None)   #データの読み込み

    return data



def write_csv(file, data_list):
    with open(file, "w", newline="") as f:
        writer = csv.writer(f)
        for data in data_list:
            writer.writerow(data)
    f.close()


    
def population(line,sum):
    p=[]
    for fi in line:   #人口分布
        p.append(fi/sum)
        
    return p


def main():
    data = read_csv( "Sanda_population_uddy.csv" )
    lst = [i for i in range(len(data))]
    s = sum (data[1])
    p = population(data[1], s)
    choice_house = random.choices(lst, k=115, weights=p)    #確率に従って抽出
    data_list = []
    for num in choice_house:
        data_list.append([data[2][num], data[3][num]])
   
    write_csv("Sanda_departure_list.csv", data_list)


if __name__ ==  "__main__":
    main()
    
    
