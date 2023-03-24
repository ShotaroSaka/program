#!/bin/zsh

EVA_num=$1
weight_1=$2
weight_2=$3
file=$4

if  [ ${EVA_num} = "h" ] ; then
    echo "EVA_num, weight_1, weight_2, system_file"
    exit
fi


tmp=${file##*/}
name=${tmp%.*}

function all_mkdir () {
    mkdir res_file
    mkdir res_file/${name}
    mkdir EVA_sim_log
    mkdir EVA_sim_log/${name}
    mkdir EVA_sim_pdf
    mkdir EVA_sim_pdf/${name}
    mkdir EVA_calc_dir
    mkdir EVA_calc_dir/${name}
}

all_mkdir

echo "sim 1"
./sim:1_x:time_y:EVnum.sh ${EVA_num} ${weight_1} ${weight_2} ${file}
echo "sim 2"
./sim:2_x:EVAid_y:EVnum.sh ${EVA_num} ${weight_1} ${weight_2} ${file} 
echo "sim 3"
./sim:3_x:weight_y:aveprice.sh ${EVA_num} ${file}
echo "sim 4"
./sim:4_x:price_y:EVnum.sh ${EVA_num} ${weight_1} ${weight_2} ${file}
