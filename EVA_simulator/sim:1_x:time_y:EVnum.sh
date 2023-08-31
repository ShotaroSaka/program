#!/Bin/zsh

EVA_num=$1
weight_1=$2
weight_2=$3
file=$4

tmp=${file##*/}
name=${tmp%.*}

# EVA_num=${name[1-9]}
if [ ${EVA_num} = "h" ] ; then
    echo "EVA_num, weight_1, weight_2, system_file"
    exit
fi


function make_res () {
    local kind=$1
    local weight=$2
    local EVA_num=$3
    local name=$4
    
    
    if [ ${kind} = S ] ; then
	cat <<EOF > ./res_file/${name}/sim:1_EVAkind:${kind}_weight:${weight}_EVAnum:${EVA_num}_model:${name}.res
xlabel: {time}
ylabel: Seller EV num
option: set style data linespoints
option: set yrange [0:25]
option: set key top left
option: set key maxrows 7

EOF
	
    elif [ ${kind} = B ] ; then
	cat <<EOF > ./res_file/${name}/sim:1_EVAkind:${kind}_weight:${weight}_EVAnum:${EVA_num}_model:${name}.res
xlabel: {time}
ylabel: Buyer EV num
option: set style data linespoints
option: set yrange [0:25]
option: set key top left
option: set key maxrows 7

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
    epstopdf ./tmp.eps ./EVA_sim_pdf/${name}/sim:1_EVkind:${EV_kind}_weight:${weight}_EVAnum:${EVA_num}_model:${name}.pdf
    rm ./tmp.eps
    open ./EVA_sim_pdf/${name}/sim:1_EVkind:${EV_kind}_weight:${weight}_EVAnum:${EVA_num}_model:${name}.pdf
}



`make_res S ${weight_1} ${EVA_num} ${name}`
`make_res B ${weight_1} ${EVA_num} ${name}`
`make_res S ${weight_2} ${EVA_num} ${name}`
`make_res B ${weight_2} ${EVA_num} ${name}`

res_1=./res_file/${name}/sim:1_EVAkind:S_weight:${weight_1}_EVAnum:${EVA_num}_model:${name}.res
res_2=./res_file/${name}/sim:1_EVAkind:B_weight:${weight_1}_EVAnum:${EVA_num}_model:${name}.res
res_3=./res_file/${name}/sim:1_EVAkind:S_weight:${weight_2}_EVAnum:${EVA_num}_model:${name}.res
res_4=./res_file/${name}/sim:1_EVAkind:B_weight:${weight_2}_EVAnum:${EVA_num}_model:${name}.res



echo "0"
./py_program/sim:1_EVnum_2.py $file ${weight_1} ${EVA_num} > ./EVA_sim_log/${name}/sim:1_weight:${weight_1}_model:${name}.txt
echo "1"
./py_program/sim:1_EVnum_2.py $file ${weight_2} ${EVA_num}> ./EVA_sim_log/${name}/sim:1_weight:${weight_2}_model:${name}.txt


txt_file_1=./EVA_sim_log/${name}/sim:1_weight:${weight_1}_model:${name}.txt
txt_file_2=./EVA_sim_log/${name}/sim:1_weight:${weight_2}_model:${name}.txt


for eva_id in `seq 0 1 $((${EVA_num}-1))`; do
    echo " " >> ${res_1}
    echo " " >> ${res_2}
    echo "name: EVA_{${eva_id}}" >> ${res_1}
    echo "name: EVA_{${eva_id}}" >> ${res_2}
    grep "EVA: ${eva_id} " ${txt_file_1} | awk '{print $4, $6}' >> ${res_1}
    grep "EVA: ${eva_id} " ${txt_file_1} | awk '{print $4, $8}' >> ${res_2}
done


for eva_id in `seq 0 1 $((${EVA_num}-1))`; do
    echo " " >> ${res_3}
    echo " " >> ${res_4}
    echo "name: EVA_{${eva_id}}" >> ${res_3}
    echo "name: EVA_{${eva_id}}" >> ${res_4}
    grep "EVA: ${eva_id} " ${txt_file_2} | awk '{print $4, $6}' >> ${res_3}
    grep "EVA: ${eva_id} " ${txt_file_2} | awk '{print $4, $8}' >> ${res_4}
done


res_to_pdf ${res_1} S ${weight_1} ${EVA_num} ${name}
res_to_pdf ${res_2} B ${weight_1} ${EVA_num} ${name}
res_to_pdf ${res_3} S ${weight_2} ${EVA_num} ${name}
res_to_pdf ${res_4} B ${weight_2} ${EVA_num} ${name}
