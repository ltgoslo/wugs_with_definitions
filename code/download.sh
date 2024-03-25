git clone https://github.com/akutuzov/rushifteval_public.git
git clone https://github.com/ltgoslo/nor_dia_change.git
wget https://zenodo.org/record/6433667/files/dwug_es.zip
wget https://zenodo.org/record/7389506/files/dwug_sv.zip
wget https://zenodo.org/record/7387261/files/dwug_en.zip
wget https://zenodo.org/record/7441645/files/dwug_de.zip
for f in *zip; do 
    unzip $f
done
rm *zip
