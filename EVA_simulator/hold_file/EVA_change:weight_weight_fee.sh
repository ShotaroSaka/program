#!/bin/zsh

name=$1
EVA_num=$2
file=$3


if [ ${name} = "h" ] ; then
    echo "name, EVA_num, system_file"
    exit
fi

function res_to_pdf () {
    res=$1
    EV_kind=$2
    name=$3

    xdoplot -te ${res} | psfix-gnuplot -e > ./tmp.eps
    epstopdf ./tmp.eps ./EVA_sim_pdf/${name}/EVkind:${EV_kind}_model:${name}.pdf
    rm ./tmp.eps
    open ./EVA_sim_pdf/${name}/EVkind:${EV_kind}_model:${name}.pdf

}

mkdir ./res_file/${name}
cat <<EOF > ./res_file/${name}/kind:S_weight:0-5_model:${name}.res
xlabel: {weight}
ylabel: Seller EV ave_price
option: set style data linespoints
option: set key top right

name: SellerAvePrice
EOF

cat <<EOF > ./res_file/${name}/kind:B_weight:0-5_model:${name}.res
xlabel: {weight}
ylabel: Buyer EV ave_price
option: set style data linespoints
option: set key top right

name: BuyerAvePrice
EOF
  

res_1=./res_file/${name}/kind:S_weight:0-5_model:${name}.res
res_2=./res_file/${name}/kind:B_weight:0-5_model:${name}.res

mkdir ./EVA_sim_log/${name}
for kappa_rate in `seq 0 1 5`; do
    ./py_program/ggg.py $file ${kappa_rate} ${EVA_num}> ./EVA_sim_log/${name}/weight:${kappa_rate}_model:${name}.txt
    echo "kappa_rate " $kappa_rate
    echo -n ${kappa_rate}>>${res_1}
    echo -n ${kappa_rate}>>${res_2}
    echo -n " ">>${res_1}
    echo -n " ">>${res_2}
    tail -n 1 ./EVA_sim_log/${name}/weight:${kappa_rate}_model:${name}.txt | awk '{print $4}'>>${res_1}
    tail -n 1 ./EVA_sim_log/${name}/weight:${kappa_rate}_model:${name}.txt | awk '{print $8}'>>${res_2}
done

mkdir ./EVA_sim_pdf/${name}
res_to_pdf ${res_1} S ${name}
res_to_pdf ${res_2} B ${name}
