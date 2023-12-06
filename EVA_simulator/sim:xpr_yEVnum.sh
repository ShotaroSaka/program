#!/bin/zsh

seed=1
EVA_num=$1
weight_1=$2
weight_2=$3
lambda=0.5
file=$4

tmp=${file##*/}
name=${tmp%.*}

if [ ${EVA_num} = "h" ] ; then
    echo "EVA_num, weight_1, weight_2, system_file"
    exit
fi

function make_res () {
    local name=$1
    local price=$2
    
    cat <<EOF > ./res_file/${name}/sim:1_price:${price}_model:${name}.res
xlabel: probability
ylabel: EV num
option: set style data linespoints
option: set key top left
option: set yrange [0:160]
EOF
}

function res_to_pdf () {
    res=$1
    name=$2

    xdoplot -te ${res} | psfix-gnuplot -e > ./tmp.eps
    epstopdf ./tmp.eps ./EVA_sim_pdf/${name}/sim:1_price:${price}_model:${name}.pdf
    rm ./tmp.eps
    open ./EVA_sim_pdf/${name}/sim:1_price:${price}_model:${name}.pdf
}    

function calc () {
    weight=$1
    txt_file=$2
    res=$3
        
    echo " " >> ${res}
    echo "name: omega:${weight}" >> ${res}
    cat ${txt_file} >> ${res}
}

for price in `seq 0.0 0.5 1.0`; do
    make_res ${name} ${price}
    res=./res_file/${name}/sim:1_price:${price}_model:${name}.res
    echo "${price}"
    for weight in `seq ${weight_1} 1 ${weight_2}`; do
	echo "${weight}"
	#./py_program/eva0821.py ${seed} ${EVA_num} ${weight} ${lambda} ${price} $file > ./EVA_sim_log/${name}/sim:1_price:${price}_weight:${weight}_model:${name}.txt
	txt_file=./EVA_sim_log/${name}/sim:1_price:${price}_weight:${weight}_model:${name}.txt
	calc ${weight} ${txt_file} ${res}
    done
    res_to_pdf ${res} ${name}
done
