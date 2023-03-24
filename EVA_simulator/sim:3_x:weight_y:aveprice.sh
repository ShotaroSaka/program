#!/bin/zsh


EVA_num=$1
file=$2

tmp=${file##*/}
name=${tmp%.*}

if [ ${EVA_num} = "h" ] ; then
    echo "EVA_num, system_file"
    exit
fi

function res_to_pdf () {
    res=$1
    EV_kind=$2
    name=$3

    xdoplot -te ${res} | psfix-gnuplot -e > ./tmp.eps
    epstopdf ./tmp.eps ./EVA_sim_pdf/${name}/sim:3_EVkind:${EV_kind}_model:${name}.pdf
    rm ./tmp.eps
    open ./EVA_sim_pdf/${name}/sim:3_EVkind:${EV_kind}_model:${name}.pdf
}

cat <<EOF > ./res_file/${name}/sim:3_kind:S_weight:0-5_model:${name}.res
xlabel: {weight}
ylabel: Seller EV ave_price
option: set style data linespoints
option: set key top right

name: SellerAvePrice
EOF

cat <<EOF > ./res_file/${name}/sim:3_kind:B_weight:0-5_model:${name}.res
xlabel: {weight}
ylabel: Buyer EV ave_price
option: set style data linespoints
option: set key top right

name: BuyerAvePrice
EOF
  

res_1=./res_file/${name}/sim:3_kind:S_weight:0-5_model:${name}.res
res_2=./res_file/${name}/sim:3_kind:B_weight:0-5_model:${name}.res


for seed in `seq 1 1 10`; do
    echo "seed "$seed
    for weight in `seq 0 1 5`; do
	./py_program/sim:3_avefee.py $file ${weight} ${EVA_num} $seed > ./EVA_sim_log/${name}/sim:3_weight:${weight}_model:${name}_seed:${seed}.txt
	echo "weight"$weight
    done
done



dir=./EVA_calc_dir/${name}

for weight in `seq 0 1 5`; do
    for seed in `seq 1 1 10`; do
	echo `tail -n 1 ./EVA_sim_log/${name}/sim:3_weight:${weight}_model:${name}_seed:${seed}.txt | awk '{print $4}'` >> ${dir}/sim:3_kind:S_weight:${weight}.txt 
	echo `tail -n 1 ./EVA_sim_log/${name}/sim:3_weight:${weight}_model:${name}_seed:${seed}.txt | awk '{print $8}'` >> ${dir}/sim:3_kind:B_weight:${weight}.txt
    done
    echo -n ${weight} >> ${res_1}
    echo -n ${weight} >> ${res_2}
    echo -n " " >> ${res_1}
    echo -n " " >> ${res_2}
    cat ${dir}/sim:3_kind:S_weight:${weight}.txt | stats -t avg,conf95 | xargs >> ${res_1}
    cat ${dir}/sim:3_kind:B_weight:${weight}.txt | stats -t avg,conf95 | xargs >> ${res_2}
done


res_to_pdf ${res_1} S ${name}
res_to_pdf ${res_2} B ${name}
