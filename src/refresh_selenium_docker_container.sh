#!/bin/bash

# remove all running containers
#for i in $(docker container ls  -aq);
for i in $(docker container ls | grep chrom | cut -f 1 -d' ')
do 
    echo "Removing selenium container: $i"
    docker stop $i
    docker rm $i
done
echo "All containers stopped"
echo "------------------------"
echo ""

# run fresh selenium docker container
# below is for Intel chip (lab computers)
#docker run -d -p 4444:4444 -v /dev/shm:/dev/shm selenium/standalone-chrome
# below is for Apple M1 ARM chip
docker run -d -p 4444:4444 -v /dev/shm:/dev/shm seleniarm/standalone-chromium

echo "New selenium docker container started and listening on port 4444"
echo "------------------------"
