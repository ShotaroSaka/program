#!/bin/zsh

EVA_num=$1
weight_1=$2
weight_2=$3
file=$4

tmp=${file##*/}
name=${tmp%.*}

if [ ${EVA_num} = "h" ] ; then
    echo "EVA_num, weight_1, weight_2, system_file"
    exit
fi


function res_to_pdf () {
    res=$1
    EV_kind=$2
    EVA_num=$3
    name=$4

    xdoplot -te ${res} | psfix-gnuplot -e > ./tmp.eps
    epstopdf ./tmp.eps ./EVA_sim_pdf/${name}/sim:2_EVkind:${EV_kind}_EVAnum:${EVA_num}_model:${name}.pdf
    rm ./tmp.eps
    open ./EVA_sim_pdf/${name}/sim:2_EVkind:${EV_kind}_EVAnum:${EVA_num}_model:${name}.pdf
}


cat <<EOF > ./res_file/${name}/sim:2_EVAkind:S_EVAnum:${EVA_num}_model:${name}.res
xlabel: EVA id
ylabel: Seller EV num
option: set style data linespoints
option: set key top right
option: set yrange [0:20]
EOF

cat <<EOF > ./res_file/${name}/sim:2_EVAkind:B_EVAnum:${EVA_num}_model:${name}.res
xlabel: EVA id
ylabel: Buyer EV num
option: set style data linespoints
option: set key top right
option: set yrange [0:20]
EOF


for seed in `seq 1 1 10`; do
    echo "seed" $seed
    ./py_program/sim:2_max.py $file ${weight_1} ${EVA_num} ${seed} > ./EVA_sim_log/${name}/sim:2_weight:${weight_1}_model:${name}_seed:${seed}.txt
    ./py_program/sim:2_max.py $file ${weight_2} ${EVA_num} ${seed} > ./EVA_sim_log/${name}/sim:2_weight:${weight_2}_model:${name}_seed:${seed}.txt
done
    


txt_file_1=./EVA_sim_log/${name}/sim:2_weight:${weight_1}_model:${name}
txt_file_2=./EVA_sim_log/${name}/sim:2_weight:${weight_2}_model:${name}

dir=./EVA_calc_dir/${name}
for seed in `seq 1 1 10`; do
    for eva_id in `seq 0 1 $((${EVA_num}-1))`; do
	echo `grep "EVA_S: ${eva_id} " ${txt_file_1}_seed:${seed}.txt | awk '{print $4}'` >> ${dir}/sim:2_kind:S_weight:${weight_1}_EVA:${eva_id}.txt
	echo `grep "EVA_S: ${eva_id} " ${txt_file_2}_seed:${seed}.txt | awk '{print $4}'` >> ${dir}/sim:2_kind:S_weight:${weight_2}_EVA:${eva_id}.txt
        echo `grep "EVA_B: ${eva_id} " ${txt_file_1}_seed:${seed}.txt | awk '{print $4}'` >> ${dir}/sim:2_kind:B_weight:${weight_1}_EVA:${eva_id}.txt
	echo `grep "EVA_B: ${eva_id} " ${txt_file_2}_seed:${seed}.txt | awk '{print $4}'` >> ${dir}/sim:2_kind:B_weight:${weight_2}_EVA:${eva_id}.txt   
    done
done



res_1=./res_file/${name}/sim:2_EVAkind:S_EVAnum:${EVA_num}_model:${name}.res
res_2=./res_file/${name}/sim:2_EVAkind:B_EVAnum:${EVA_num}_model:${name}.res

for weight in `seq 0 5 5`; do
    echo " " >> ${res_1}
    echo " " >> ${res_2}
    echo "name: S weight:${weight}" >> ${res_1}
    echo "name: B weight:${weight}" >> ${res_2}

    for eva_id in `seq 0 1 $((${EVA_num}-1))`; do
	echo -n ${eva_id} >> ${res_1}
	echo -n ${eva_id} >> ${res_2}
	echo -n " " >> ${res_1}
	echo -n " " >> ${res_2}
	cat ${dir}/sim:2_kind:S_weight:${weight}_EVA:${eva_id}.txt | stats -t avg,conf95 | xargs >> ${res_1}
	cat ${dir}/sim:2_kind:B_weight:${weight}_EVA:${eva_id}.txt | stats -t avg,conf95 | xargs >> ${res_2}
    done
done


res_to_pdf ${res_1} S ${EVA_num} ${name}
res_to_pdf ${res_2} B ${EVA_num} ${name}
