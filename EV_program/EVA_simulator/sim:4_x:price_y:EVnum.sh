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

function make_res () {
    local kind=$1
    local name=$2
    
    
    if [ ${kind} = S ] ; then
	cat <<EOF > ./res_file/${name}/sim:4_EVAkind:${kind}_model:${name}.res
xlabel: {price}
ylabel: Seller EV num
option: set style data linespoints
option: set key top left
EOF
	
    elif [ ${kind} = B ] ; then
	cat <<EOF > ./res_file/${name}/sim:4_EVAkind:${kind}_model:${name}.res
xlabel: {price}
ylabel: Buyer EV num
option: set style data linespoints
option: set key top left
EOF
	
    fi
}


function calc () {
    weight=$1
    txt_file=$2
    res_S=$3
    res_B=$4

    echo " " >> ${res_S}
    echo " " >> ${res_B}
    echo "name: kind:S_weight:${weight}_price" >> ${res_S}
    echo "name: kind:B_weight:${weight}_price " >> ${res_B}
    echo "1"
    echo $txt_file
    for n in `seq 0 1 99`; do
	a=`grep "S_${n}:" ${txt_file}_seed:1.txt | awk '{print $2}'`
	b=`grep "B_${n}:" ${txt_file}_seed:1.txt | awk '{print $3}'`
	ave=$(($(($a+$b))/2))
	echo -n $ave >> ${res_S}
	echo -n $ave >> ${res_B}
	echo -n " " >> ${res_S}
	echo -n " " >> ${res_B}
	sum_S=0
	sum_B=0

	for seed in `seq 1 1 5`; do
	    c=`grep "S_${n}:" ${txt_file}_seed:${seed}.txt | awk '{print $5}'`
	    sum_S=$((${sum_S}+${c}))
	    d=`grep "B_${n}:" ${txt_file}_seed:${seed}.txt | awk '{print $5}'`
	    sum_B=$((${sum_B}+${d}))
	done
	
	echo $sum_S >> ${res_S}
	echo $sum_B >> ${res_B}
    done
}


function res_to_pdf () {
    res=$1
    EV_kind=$2
    name=$3

    xdoplot -te ${res} | psfix-gnuplot -e > ./tmp.eps
    epstopdf ./tmp.eps ./EVA_sim_pdf/${name}/sim:4_EVkind:${EV_kind}_model:${name}.pdf
    rm ./tmp.eps
    open ./EVA_sim_pdf/${name}/sim:4_EVkind:${EV_kind}_model:${name}.pdf
}    


make_res S ${name}
make_res B ${name}


for seed in `seq 1 1 5`; do
    echo "seed_"$seed
    ./py_program/sim:4_hist.py $file ${weight_1} ${EVA_num} ${seed} > ./EVA_sim_log/${name}/sim:4_weight:${weight_1}_model:${name}_seed:${seed}.txt
    ./py_program/sim:4_hist.py $file ${weight_2} ${EVA_num} ${seed} > ./EVA_sim_log/${name}/sim:4_weight:${weight_2}_model:${name}_seed:${seed}.txt
done 


res_S=./res_file/${name}/sim:4_EVAkind:S_model:${name}.res
res_B=./res_file/${name}/sim:4_EVAkind:B_model:${name}.res

txt_file_1=./EVA_sim_log/${name}/sim:4_weight:${weight_1}_model:${name}
txt_file_2=./EVA_sim_log/${name}/sim:4_weight:${weight_2}_model:${name}

calc ${weight_1} ${txt_file_1} ${res_S} ${res_B}
calc ${weight_2} ${txt_file_2} ${res_S} ${res_B}


res_to_pdf ${res_S} S ${name}
res_to_pdf ${res_B} B ${name}
