#!/bin/zsh

EVA_num=$1
weight_1=$2
weight_2=$3
name=$4
file=$5

if [ ${EVA_num} = "h" ] ; then
    echo "EVA_num, weight_1, weight_2, name, system_file"
    exit
fi


function make_res () {
    local kind=$1
    local weight=$2
    local EVA_num=$3
    local name=$4
    
    
    if [ ${kind} = S ] ; then
	cat <<EOF > ./res_file/${name}/sim:4_EVAkind:${kind}_weight:${weight}_EVAnum:${EVA_num}_model:${name}_hist.res
xlabel: {price}
ylabel: Seller EV num
option: set style data linespoints
option: set key top left

name: EV-S-rate-hist

EOF
	
    elif [ ${kind} = B ] ; then
	cat <<EOF > ./res_file/${name}/sim:4_EVAkind:${kind}_weight:${weight}_EVAnum:${EVA_num}_model:${name}_hist.res
xlabel: {price}
ylabel: Buyer EV num
option: set style data linespoints
option: set key top left

name: EV-B-rate-hist

EOF
	
    fi
}


function res_to_pdf () {
    res=$1
    EV_kind=$2
    weight=$3
    EVA_num=$4
    name=$5

    xdoplot -te ${res} | psfix-gnuplot -e > ./tmp.eps
    epstopdf ./tmp.eps ./EVA_sim_pdf/${name}/sim:4_EVkind:${EV_kind}_weight:${weight}_EVAnum:${EVA_num}_model:${name}_hist.pdf
    rm ./tmp.eps
    open ./EVA_sim_pdf/${name}/sim:4_EVkind:${EV_kind}_weight:${weight}_EVAnum:${EVA_num}_model:${name}_hist.pdf
}


mkdir ./res_file/${name}
`make_res S ${weight_1} ${EVA_num} ${name}`
`make_res S ${weight_2} ${EVA_num} ${name}`
`make_res B ${weight_1} ${EVA_num} ${name}`
`make_res B ${weight_2} ${EVA_num} ${name}`

res_1=./res_file/${name}/sim:4_EVAkind:S_weight:${weight_1}_EVAnum:${EVA_num}_model:${name}_hist.res
res_2=./res_file/${name}/sim:4_EVAkind:S_weight:${weight_2}_EVAnum:${EVA_num}_model:${name}_hist.res
res_3=./res_file/${name}/sim:4_EVAkind:B_weight:${weight_1}_EVAnum:${EVA_num}_model:${name}_hist.res
res_4=./res_file/${name}/sim:4_EVAkind:B_weight:${weight_2}_EVAnum:${EVA_num}_model:${name}_hist.res


mkdir ./EVA_sim_log/${name}

for seed in `seq 1 1 2`; do
    echo "seed_"$seed
    ./py_program/sim:4_hist.py $file ${weight_1} ${EVA_num} ${seed} > ./EVA_sim_log/${name}/sim:4_weight:${weight_1}_model:${name}_seed:${seed}.txt
    ./py_program/sim:4_hist.py $file ${weight_2} ${EVA_num} ${seed} > ./EVA_sim_log/${name}/sim:4_weight:${weight_2}_model:${name}_seed:${seed}.txt
done 

txt_file_1=./EVA_sim_log/${name}/sim:4_weight:${weight_1}_model:${name}
txt_file_2=./EVA_sim_log/${name}/sim:4_weight:${weight_2}_model:${name}

for n in `seq 0 1 99`; do
    a=`grep "S_${n}:" ${txt_file_1}_seed:1.txt | awk '{print $2}'`
    b=`grep "S_${n}:" ${txt_file_1}_seed:1.txt | awk '{print $3}'`
    ave=$(($(($a+$b))/2))
    echo -n $ave >> ${res_1}
    echo -n $ave >> ${res_2}
    echo -n " " >> ${res_1}
    echo -n " " >> ${res_2}
    sum_S_0=0
    sum_S_5=0
    for seed in `seq 1 1 2`; do
	c=`grep "S_${n}:" ${txt_file_1}_seed:${seed}.txt | awk '{print $5}'`
	sum_S_0=$((${sum_S_0}+${c}))
	d=`grep "S_${n}:" ${txt_file_2}_seed:${seed}.txt | awk '{print $5}'`
	sum_S_5=$((${sum_S_5}+${d}))
    done
    echo $sum_S_0 >> ${res_1}
    echo $sum_S_5 >> ${res_2}
done


for n in `seq 0 1 99`; do
    a=`grep "B_${n}:" ${txt_file_1}_seed:1.txt | awk '{print $2}'`
    b=`grep "B_${n}:" ${txt_file_1}_seed:1.txt | awk '{print $3}'`
    ave=$(($(($a+$b))/2))
    echo -n $ave >> ${res_3}
    echo -n $ave >> ${res_4}
    echo -n " " >> ${res_3}
    echo -n " " >> ${res_4}
    sum_B_0=0
    sum_B_5=0
    for seed in `seq 1 1 5`; do
	c=`grep "B_${n}:" ${txt_file_1}_seed:${seed}.txt | awk '{print $5}'`
	sum_B_0=$((${sum_B_0}+${c}))
	d=`grep "B_${n}:" ${txt_file_2}_seed:${seed}.txt | awk '{print $5}'`
	sum_B_5=$((${sum_B_5}+${d}))
    done
    echo $sum_B_0 >> ${res_3}
    echo $sum_B_5 >> ${res_4}
done


mkdir ./EVA_sim_pdf/${name}
res_to_pdf ${res_1} S ${weight_1} ${EVA_num} ${name}
res_to_pdf ${res_2} S ${weight_2} ${EVA_num} ${name}
res_to_pdf ${res_3} B ${weight_1} ${EVA_num} ${name}
res_to_pdf ${res_4} B ${weight_2} ${EVA_num} ${name}
