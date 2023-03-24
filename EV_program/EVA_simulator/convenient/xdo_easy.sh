#!/bin/zsh

res_file=$1

tmp=${res_file##*/}
name=${tmp%.*}

xdoplot -te ${res_file} | psfix-gnuplot -e > tmp.eps
epstopdf tmp.eps ${name}.pdf
rm tmp.eps
open ${name}.pdf
