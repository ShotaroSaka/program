#!/Bin/zsh

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
    local price=$1
    local weight=$2
     
    cat <<EOF > ./res_file/${name}/sim:2_EVkind:S_weight:${weight}_preP:${price}_model:${name}.res
xlabel: {time}
ylabel: Number of Seller EVs 
option: set style data linespoints
option: set xrange [0:10]
option: set yrange [0:15]
option: set key top left

EOF
    
    cat <<EOF > ./res_file/${name}/sim:2_EVkind:B_weight:${weight}_preP:${price}_model:${name}.res
xlabel: {time}
ylabel: Number of Buyer EVs 
option: set style data linespoints
option: set xrange [0:10]
option: set yrange [0:15]
option: set key top left

EOF
}

function calc () {
    res_S=$1
    res_B=$2
    txt_file=$3
    
    for eva_id in `seq 0 1 $((${EVA_num}-1))`; do
	echo " " >> ${res_S}
	echo " " >> ${res_B}
	echo "name: EVA_{${eva_id}}" >> ${res_S}
	echo "name: EVA_{${eva_id}}" >> ${res_B}
	grep "EVA: ${eva_id} " ${txt_file} | awk '{print $4, $6}' >> ${res_S}
	grep "EVA: ${eva_id} " ${txt_file} | awk '{print $4, $8}' >> ${res_B}
    done
}
    
function res_to_pdf () {
    EV_kind=$1
    weight=$2
    price=$3

    res=./res_file/${name}/sim:2_EVkind:${EV_kind}_weight:${weight}_preP:${price}_model:${name}.res
    xdoplot -te ${res} | psfix-gnuplot -e > ./tmp.eps
    epstopdf ./tmp.eps ./EVA_sim_pdf/${name}/sim:2_EVkind:${EV_kind}_weight:${weight}_preP:${price}_model:${name}.pdf
    rm ./tmp.eps
    open ./EVA_sim_pdf/${name}/sim:2_EVkind:${EV_kind}_weight:${weight}_preP:${price}_model:${name}.pdf
}

for price in `seq 0 0.5 1.0`; do
    make_res ${price} ${weight_1}
    res_S=./res_file/${name}/sim:2_EVkind:S_weight:${weight_1}_preP:${price}_model:${name}.res
    res_B=./res_file/${name}/sim:2_EVkind:B_weight:${weight_1}_preP:${price}_model:${name}.res

    echo "${price}"
    ./py_program/eva0821.py ${seed} ${EVA_num} ${weight_1} ${lambda} ${price} $file  > ./EVA_sim_log/${name}/sim2_weight:${weight_1}_preP:${price}_model:${name}.txt
    txt_file=./EVA_sim_log/${name}/sim2_weight:${weight_1}_preP:${price}_model:${name}.txt

    calc ${res_S} ${res_B} ${txt_file}
done

for price in `seq 0 0.5 1.0`; do
    make_res ${price} ${weight_2}
    res_S=./res_file/${name}/sim:2_EVkind:S_weight:${weight_2}_preP:${price}_model:${name}.res
    res_B=./res_file/${name}/sim:2_EVkind:B_weight:${weight_2}_preP:${price}_model:${name}.res

    echo "${price}"
    ./py_program/eva0821.py ${seed} ${EVA_num} ${weight_2} ${lambda} ${price} $file  > ./EVA_sim_log/${name}/sim:2_weight:${weight_2}_preP:${price}_model:${name}.txt
    txt_file=./EVA_sim_log/${name}/sim:2_weight:${weight_2}_preP:${price}_model:${name}.txt

    calc ${res_S} ${res_B} ${txt_file}
done

for price in `seq 0 0.5 1.0`; do
    res_to_pdf S ${weight_1} ${price} 
    res_to_pdf S ${weight_2} ${price}
    res_to_pdf B ${weight_1} ${price}
    res_to_pdf B ${weight_2} ${price} 
done
