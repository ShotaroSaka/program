#!/bin/zsh

function exection {
    local lambda=$1
    local EVA_num=$2
    local frequency=$3
    local file=$4
    
    for seed in `seq 1 1 4`; do
	echo "seed" $seed
	for weight in `seq 0 1 5`; do
	    echo "weight" $weight
	    log_txt=./EVA_sim_log/${name}/sim:2_model:${name}_weight:${weight}_seed:${seed}.txt
	    ./py_program/eva.py ${seed} ${weight} ${lambda} ${EVA_num} ${frequency} ${file} > ${log_txt}
	done
    done
}    


function make_res () {
    local name=$1
    
    cat <<EOF > ./res_file/${name}/sim:2_EVkind:S_model:${name}.res
xlabel: /omega
ylabel: Seller EV num
option: set style data linespoints
option: set yrange [0:30]
option: set key top left
option: set key maxrows 7

EOF
     
    cat <<EOF > ./res_file/${name}/sim:2_EVkind:B_model:${name}.res
xlabel: /omega
ylabel: Buyer EV num
option: set style data linespoints
option: set yrange [0:30]
option: set key top left
option: set key maxrows 7

EOF
}



function max_calc {
    local EVA_num=$1
    
    dir=./EVA_calc_dir/${name}
    for weight in `seq 0 1 5`; do
	echo -n "" > ${dir}/sim:2_kind:S_weight:${weight}.txt
	echo -n "" > ${dir}/sim:2_kind:B_weight:${weight}.txt
	for seed in `seq 1 1 4`; do
	    log_file=./EVA_sim_log/${name}/sim:2_model:${name}_weight:${weight}_seed:${seed}.txt
	    echo `grep "EVA_S:" $log_file | awk '{print $4}'` >> ${dir}/sim:2_kind:S_weight:${weight}.txt
	    echo `grep "EVA_B:" $log_file | awk '{print $4}'` >> ${dir}/sim:2_kind:B_weight:${weight}.txt
	done
    done

    res_S=./res_file/${name}/sim:2_EVkind:S_model:${name}.res
    res_B=./res_file/${name}/sim:2_EVkind:B_model:${name}.res
    for eva_id in `seq 1 1 ${EVA_num}`; do
	echo "name: EVAid ${eva_id}" >> ${res_S}
	echo "name: EVAid ${eva_id}" >> ${res_B}
	for weight in `seq 0 1 5`; do
	    echo -n "${weight} " >> ${res_S}
	    echo -n "${weight} " >> ${res_B}
	    cat ${dir}/sim:2_kind:S_weight:${weight}.txt | awk -v col="$eva_id" '{print $col}'| stats -t avg,conf95 | xargs >> ${res_S}
	    cat ${dir}/sim:2_kind:B_weight:${weight}.txt | awk -v col="$eva_id" '{print $col}'| stats -t avg,conf95 | xargs >> ${res_B}
	done
    done
}



file=$1
lambda=0.4
frequency=20

tmp=${file##*/}
name=${tmp%.*}
EVA_num=$(echo "${name}" | awk -F: '{print $NF}')


make_res ${name} 
if [ ! -e ./EVA_sim_log/${name}/sim:2_model:${name}_weight:5_seed:1.txt ]; then
    exection ${lambda} ${EVA_num} ${frequency} ${file}
    max_calc ${EVA_num}
else
    max_calc ${EVA_num}
fi
