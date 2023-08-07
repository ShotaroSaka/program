#!/bin/zsh

file_1=$1
file_2=$2
file_3=$3
tmp_1=${file_1##*/}
tmp_2=${file_2##*/}
tmp_3=${file_3##*/}
name_1=${tmp%.*}
name_2=${tmp%.*}
name_3=${tmp%.*}

function all_mkdir () {
    if [ -d res_file ] ; then 
	mkdir res_file
	mkdir res_file/${name_1}
	mkdir res_file/${name_2}
	mkdir res_file/${name_3}
    if [ -d EVA_sim_log ] ; then
	mkdir EVA_sim_log
	mkdir EVA_sim_log/${name_1}
	mkdir EVA_sim_log/${name_2}
	mkdir EVA_sim_log/${name_3}
    if [ -d EVA_sim_pdf ] ; then
	mkdir EVA_sim_pdf
	mkdir EVA_sim_pdf/${name_1}
	mkdir EVA_sim_pdf/${name_2}
	mkdir EVA_sim_pdf/${name_3}
    if [ -d EVA_sim_pdf ] ; then
	mkdir EVA_calc_dir
	mkdir EVA_calc_dir/${name_1}
	mkdir EVA_calc_dir/${name_2}
	mkdir EVA_calc_dir/${name_3}
}


all_mkdir
echo "${file_1}"
./max_EVAnum.sh ${file_1}
echo "${file_2}"
./max_EVAnum.sh ${file_2}
echo "${file_3}"
./max_EVAnum.sh ${file_3}






