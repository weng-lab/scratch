#!/bin/bash

mkdir -p purcaroFimoTest
cd purcaroFimoTest

# download a DNase-seq bigwig file from Encode
# from experiment https://www.encodeproject.org/experiments/ENCSR000ENP/
wget -c https://www.encodeproject.org/files/ENCFF001BDH/@@download/ENCFF001BDH.bigWig

# I'm just testing on chr7; convert bigWig to wig and extract chr7
wget -c http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64.v287/bigWigToWig
chmod u+x bigWigToWig
./bigWigToWig -chrom=chr7 ENCFF001BDH.bigWig ENCFF001BDH.chr7.wig

# grab chr7
wget -c http://hgdownload.cse.ucsc.edu/goldenpath/hg19/chromosomes/chr7.fa.gz
gunzip chr7.fa.gz
size=$(~/bin/fimo_4.10/bin/getsize -l chr7.fa) # Calculate size of sequence file

# create priors
~/bin/fimo_4.10/bin/create-priors --seq-size $size --alpha 1 --beta 10000 -oc Prior --num-bins 1000 ./ENCFF001BDH.chr7.wig

# using CTCF from JASPAR 2014 from MEME site
wget -c http://ebi.edu.au/ftp/software/MEME/Databases/motifs/motif_databases.12.1.tgz
tar zxvf motif_databases.12.1.tgz

# run fimo
~/bin/fimo_4.10/bin/fimo --thresh 0.05 --text --parse-genomic-coord --psp ./Prior/priors.wig --prior-dist ./Prior/priors.dist --motif MA0139.1 ./motif_databases/JASPAR_CORE_2014_vertebrates.meme ./chr7.fa > fimo.priors.chr7.txt

grep -P '[+-]\t[^-]' ./fimo.priors.chr7.txt | wc -l
