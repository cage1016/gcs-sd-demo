# assing google cloud storage testing loop
num_loop=10

standard_bucket="gcs-sd-demo-standard"
nearline_bucket="gcs-sd-demo-nearline"

files[0]="Hallstatt, Austria.jpg" #4.37.59KB
files[1]="HBase Essentials.pdf" #2.06MB
files[2]="Google BigQuery Analytics.pdf" # 8.35mb

measure_download() {
    echo -e "\n__$1__"
    echo -e "start measure google cloud storage file download: x ${num_loop}"

    for (( i = 0 ; i < ${#files[@]} ; i++ )) do
        for (( j=1; j<=$num_loop; j=j+1 ))
        do
            file="${files[$i]}"
            file_name="${file%%.*}_${j}.${file#*.}"
            echo -e "\nfile: ${file}, loop: ${j}"
            python transfer.py "gs://$1/$file" "./docs/$file_name"
        done
    done
}

measure_download $standard_bucket
measure_download $nearline_bucket
