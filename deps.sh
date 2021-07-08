ops build $1
sudo virt-install --connect=qemu:///system \
    --name=$2 \
    --ram=128 \
    --vcpu=1 \
    --disk path=/home/$USER/.ops/images/$1.img,format=raw \
    --import \
    --network network:default \
    --vnc