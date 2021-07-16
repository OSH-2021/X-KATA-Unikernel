# Ceph部署文档（单机版，分布式，docker）

本篇部署文档基于

https://blog.csdn.net/qq_35957624/article/details/78669103 作者：皮皮鲁666

排除了一些部署中遇到的小bug。

我们小组先挑战了分布式，然后再进行单机版就轻松了很多，docker的很多步骤和分布式差不多。

## 分布式部署

### 一、节点规划

三节点Centos7主机，其中ceph-admin节点为管理节点和监控节点，ceph-1、ceph-client为osd节点，每个节点3个磁盘（分别命名为sda、sdb、sdc）；sda作为系统盘，sdb，sdc，作为OSD存储。ceph-client同时为客户端，方便以后进行存储测试。所有节点都安装CeontOS7。

| **主机**    | **IP**         | **功能**                                                |
| ----------- | -------------- | ------------------------------------------------------- |
| ceph-admin  | 192.168.43.100 | ceph-deploy、mon、ntp server                            |
| ceph-1      | 192.168.43.101 | osd.0、mds                                              |
| ceph-client | 192.168.43.103 | osd.1、客户端，主要利用它挂载ceph集群提供的存储进行测试 |

为虚拟机添加硬盘很简单，只需在虚拟机设置里添加即可，本实验不需要手动挂载分区。

### 二、前期准备，安装ceph-deploy工具

所有的节点都是root用户登录的。 

#### 1、修改每个节点的主机名，并重启。

```shell
 hostnamectl set-hostname ceph-admin (ceph-1/ceph-client)
```

#### 2、配置防火墙启动端口

需要在每个节点上执行以下命令：

```shell
 firewall-cmd --zone=public --add-port=6789/tcp --permanent

 firewall-cmd --zone=public --add-port=6800-7100/tcp --permanent

 firewall-cmd --reload

 firewall-cmd --zone=public --list-all
```

#### 3、禁用selinux

需要在每个节点上执行以下命令：

```shell
 setenforce 0

 vim /etc/selinux/config
```

将SELINUX设置为disabled

#### 4、配置ceph-admin节点的hosts文件

vi /etc/hosts

```shell
192.168.43.100  ceph-admin

192.168.43.101  ceph-1

192.168.43.103  ceph-client
```

### 三、配置ceph-admin部署节点的无密码登录每个ceph节点

#### 0、确保网络连接

以下针对所有节点，

如果使用虚拟机，比如VMWare，需要网络适配器设置为桥接，并且不勾选复制物理地址。

在虚拟网络编辑器中

将`VMnet0`（默认为桥接使用的端口），桥接至实机网卡。

重启系统，输入

```shell
 vim /etc/sysconfig/network-scripts/ifcfg-ens33
```

![setting](files\setting.jpg)

将`IPADDR = 192.168.43.10x`

​    `GATEWAY=192.168.43.1`

替换上图

保存退出，输入

```shell
systemctl restart network
```

#### 1、在每个节点上安装一个SSH服务器

需要在每个节点上执行以下命令：

```shell
yum install openssh-server -y
```

#### 2、配置ceph-admin管理节点与每个ceph节点无密码的SSH访问

```shell
ssh-keygen
```

#### 3、复制ceph-admin节点的密钥到每个ceph节点

```shell
ssh-copy-id root@ceph-1

ssh-copy-id root@ceph-2

ssh-copy-id root@ceph-client
```

#### 4、测试每个节点不用密码是否可以登录

```shell
ssh root@ceph-1

ssh root@ceph-2

ssh root@ceph-client
```

#### 5、修改ceph-admin管理节点的~/.ssh/config文件

```shell
vi .ssh/config
```

```shell
Host ceph-admin
	Hostname ceph-admin
	User root 
Host ceph-1
	Hostname ceph-1
	User root
Host ceph-2
	Hostname ceph-2
	User root
Host ceph-client
	Hostname ceph-client
	User root
```

### 四、yum源及ceph的安装
需要在每个节点（ceph-admin/1/2/client）上执行以下命令：

```shell
yumclean all

rm -rf /etc/yum.repos.d/*.repo

wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo

wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo

sed -i '/aliyuncs/d' /etc/yum.repos.d/CentOS-Base.repo

sed -i '/aliyuncs/d' /etc/yum.repos.d/epel.repo

sed -i 's/$releasever/7/g' /etc/yum.repos.d/CentOS-Base.repo
```

#### 1、增加ceph的源
```shell
vim /etc/yum.repos.d/ceph.repo
```
添加以下内容：
```shell
[ceph]

name=ceph

baseurl=http://mirrors.163.com/ceph/rpm-jewel/el7/x86_64/

gpgcheck=0

[ceph-noarch]

name=cephnoarch

baseurl=http://mirrors.163.com/ceph/rpm-jewel/el7/noarch/

gpgcheck=0
```
#### 2、安装ceph客户端
```shell
yum makecache
yum install ceph ceph-radosgw rdate -y
```

### 五、配置NTP
我们把NTP Server放在ceph-admin节点上，其余两个ceph-1/2/client节点都是NTP Client，目的是从根本上解决时间同步问题。

#### 1、 在ceph-admin节点上
##### a、修改/etc/ntp.conf，注释掉默认的四个server，添加三行配置如下：
```shell
vim /etc/ntp.conf
```

```shell
###comment following lines:

#server 0.centos.pool.ntp.org iburst

#server 1.centos.pool.ntp.org iburst

#server 2.centos.pool.ntp.org iburst

#server 3.centos.pool.ntp.org iburst

###add following lines:

server 127.127.1.0 minpoll 4

fudge 127.127.1.0 stratum 0

#这一行需要根据client的IP范围设置。

restrict 192.168.56.0 mask 255.255.255.0 nomodify notrap
```
##### b、修改/etc/ntp/step-tickers文件如下：
```shell
 vim /etc/ntp/step-tickers
```
```
# List of NTP servers used by the ntpdateservice.

# 0.centos.pool.ntp.org

127.127.1.0
```
##### c、重启ntp服务，并查看server端是否运行正常，正常的标准就是ntpq-p指令的最下面一行是*：
```shell
 systemctl enable ntpd

 systemctl restart ntpd

 ntpq -p
```
```
remote           refid      st t when poll reach   delay  offset  jitter

*LOCAL(0)        .LOCL.           0 l    -  16    1    0.000   0.000   0.000
```
至此，NTP Server端已经配置完毕，下面开始配置Client端。

#### 2、 在ceph-1/ceph-client两个节点上
##### a、修改/etc/ntp.conf，注释掉四行server，添加一行server指向ceph-admin:
```shell
 vim /etc/ntp/conf
```
```

#server 0.centos.pool.ntp.org.iburst

#server 1.centos.pool.ntp.org.iburst

#server 2.centos.pool.ntp.org.iburst

#server 3.centos.pool.ntp.org.iburst

 

server 192.168.56.100
```
##### b、重启ntp服务并观察client是否正确连接到server端，同样正确连接的标准是ntpq-p的最下面一行以*号开头:
```shell
 systemctl enable ntpd

 systemctl restart ntpd

 ntpq -p
```
```
remote           refid      st t when poll reach   delay  offset  jitter

*ceph-admin     .LOCL.      1 u    1  64    1    0.329   0.023   0.000
```

### 六、部署Ceph

在部署节点(`ceph-admin`)安装ceph-deploy，**下文的部署节点统一指ceph-admin**:

#### 1、 在ceph-admin节点上安装ceph部署工具，并检查版本号

```shell
yum -y install ceph-deploy

ceph-deploy–version

ceph -v
```

#### 2、在部署节点（ceph-admin）创建部署目录

```shell
mkdir cluster

cd /cluster
```

#### 3、创建以ceph-admin为监控节点的集群

```shell
ceph-deploy new ceph-admin
```

#### 4、完成后，查看目录内容

```shell
ls
```

ceph.conf  ceph.deploy-ceph.log   ceph.mon.keyring

#### 5、编辑admin-node节点的ceph配置文件，把下面的配置放入ceph.conf中

```shell
vim ceph.conf

osd pool default size = 4//根据具体的osd数量，这里是4
```

#### 6、初始化mon节点并收集keyring
```shell
 ceph-deploy mon create-initial

…….

…….

 ls
```
ceph.bootstrap-mds.keyring  ceph.bootstrap-rgw.keyring  ceph.conf   ceph.mon.keyring

ceph.bootstrap-osd.keyring  ceph.client.admin.keyring  ceph-deploy-ceph.log

#### 7、把ceph-admin节点的配置文件与keyring同步至其它节点：
```shell
ceph-deploy adminceph-admin ceph-1 ceph-2 ceph-client
```
#### 8、查看集群状态
```shell
ceph -s
```
这个时候出现 ` health HEALTH_ERR` , 我们还没有部署OSD

#### 9、开始部署OSD
```shell
ceph-deploy --overwrite-conf osd prepare ceph-1:/dev/sdb ceph-client:/dev/sdb --zap-disk
```
```shell
ceph-deploy --overwrite-conf osd activate ceph-1:/dev/sdb ceph-client:/dev/sdb
```
这时候可能会出现`ceph Cannot discover filesystem type: device /dev/sdb: Line is truncated:`的错误，如果最后ceph -s发现集群正确构建了，则不需理睬。否则请见这篇文章修改
 > https://www.cnblogs.com/menkeyi/p/6980041.html

#### 10、查看集群状态

这个时候出现 ` health HEALTH_WARN`

![ceph_warn](files\ceph_warn.png)

#### 11、增加rbd池的PG，去除WARN
```shell
ceph osd pool set rbd pg_num 128

ceph osd pool set rbd pgp_num 128
```
#### 12、添加一个元数据服务器
```shell
ceph-deploy mds create ceph-1
```
#### 13、再次查看集群状态

这个时候出现 ` health HEALTH_OK`
显示` 128 active+clean` 即可

![ceph_4osd](files\ceph_4osd.png)

## 单机版

在分布式的基础上，单机版就非常简单了。

由于只需要一个admin节点，所以不管ceph-1，ceph-client

### 1.在admin上添加两个OSD

因为ceph默认两个是最小的size
```shell
ceph-deploy --overwrite-conf osd prepare ceph-admin:/dev/sdb ceph-admin:/dev/sdc --zap-disk
```

```shell
ceph-deploy --overwrite-conf osd activate ceph-admin:/dev/sdb ceph-admin:/dev/sdc
```

### 2.在分布式的基础上，删除其余节点的osd

#### a.降osd权重

先降低osd权重为0，让数据自动迁移至其它osd，可避免out和crush remove操作时的两次水位平衡。

水位平衡完成后，即用ceph -s查看到恢复HEALTH_OK状态后，再继续后续操作。

x=0,1,2,3

```
ceph osd crush reweight osd.x 0
watch -n3 -d ceph -s
```

#### b.停osd服务

登录对应节点，停止osd服务。

```shell
ssh root@ceph-1(ceph-client)
systemctl stop ceph-osd@x.service
```

x=0,1对应ceph-1，x=2,3对应ceph-client

#### c.标记osd为out

```
ceph osd out osd.x
```

#### d.删除crush map中的osd

```shell
ceph osd crush remove osd.x
```

#### e.删除osd

```shell
ceph osd rm osd.x
```

#### f.删除Host

删除掉crush map中已没有osd的host。

```shell
ceph osd crush remove ceph-1(ceph-client)
```

### 3.查看集群状态

自我调整需要一段时间

```shell
ceph -s
```

![ceph_healthok](files\ceph_healthok.png)

部署完成



## docker部署

部署的思路和网络架构和前面分布式是一样的，区别在于命令的形式。

### 在每个节点安装 docker

登录 https://cr.console.aliyun.com/#/accelerator 获取自己的阿里云 docker 加速地址

#### 1. 安装升级 docker 客户端

```shell
curl -sSL http://acs-public-mirror.oss-cn-hangzhou.aliyuncs.com/docker-engine/internet | sh -
```

#### 2. 使用 docker 加速器

可以通过修改 daemon 配置文件 /etc/docker/daemon.json 来使用加速器，注意修改使用自己的加速地址 

```shell
mkdir -p /etc/docker
tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": ["https://******.mirror.aliyuncs.com"]
}
EOF
systemctl daemon-reload
systemctl restart docker
systemctl enable docker
```

### 启动 MON

#### 1. 下载 ceph daemon 镜像

```shell
docker pull ceph/daemon
```

#### 2. 启动 mon

 在 ceph-admin 上启动 mon,注意修改 MON_IP 

```shell
 docker run -d \
        --net=host \
        -v /etc/ceph:/etc/ceph \
        -v /var/lib/ceph/:/var/lib/ceph/ \
        -e MON_IP=192.168.43.100 \
        -e CEPH_PUBLIC_NETWORK=192.168.43.0/24 \
        ceph/daemon mon
```

#### 3.查看集群状态 

```shell
 docker exec b79a02 ceph -s
    cluster 96ae62d2-2249-4173-9dee-3a7215cba51c
     health HEALTH_ERR
            no osds
     monmap e2: 1 mons at {ceph-admin=192.168.43.100:6789/0}
            election epoch 4, quorum 0 ceph-admin
        mgr no daemons active 
     osdmap e1: 0 osds: 0 up, 0 in
            flags sortbitwise,require_jewel_osds,require_kraken_osds
      pgmap v2: 64 pgs, 1 pools, 0 bytes data, 0 objects
            0 kB used, 0 kB / 0 kB avail
                  64 creating
```

### 启动 OSD

每台虚拟机准备了两块磁盘/dev/sdb /dev/sdc作为 osd,分别加入到集群,注意修改磁盘 

```shell
 docker run -d \
        --net=host \
        -v /etc/ceph:/etc/ceph \
        -v /var/lib/ceph/:/var/lib/ceph/ \
        -v /dev/:/dev/ \
        --privileged=true \
        -e OSD_FORCE_ZAP=1 \
        -e OSD_DEVICE=/dev/sdb \
        ceph/daemon osd_ceph_disk
```

```shell
docker run -d \
        --net=host \
        -v /etc/ceph:/etc/ceph \
        -v /var/lib/ceph/:/var/lib/ceph/ \
        -v /dev/:/dev/ \
        --privileged=true \
        -e OSD_FORCE_ZAP=1 \
        -e OSD_DEVICE=/dev/sdc \
        ceph/daemon osd_ceph_disk
```

按照同样方法将 ceph-client  的 sdb、sdc 都加入集群

查看集群

```shell
docker exec b79a02 ceph -s
    cluster 96ae62d2-2249-4173-9dee-3a7215cba51c
     health HEALTH_OK
     monmap e4: 1 mons at {ceph-admin=192.168.43.100:6789/0}
            election epoch 4, quorum 0 ceph-admin
        mgr no daemons active 
     osdmap e63: 4 osds: 4 up, 4 in
            flags sortbitwise,require_jewel_osds,require_kraken_osds
      pgmap v157: 64 pgs, 1 pools, 0 bytes data, 0 objects
            212 MB used,  25343 MB / 25555 MB avail
                  64 active+clean
```

可以看到 mon 和 osd 都已经正确配置，切集群状态为 HEALTH_OK

### 创建 MDS

使用以下命令在 ceph-admin 上启动 mds 

```shell
docker run -d \
        --net=host \
        -v /etc/ceph:/etc/ceph \
        -v /var/lib/ceph/:/var/lib/ceph/ \
        -e CEPHFS_CREATE=1 \
        ceph/daemon mds
```

### 启动 RGW ,并且映射 80 端口

使用以下命令在 ceph-admin 上启动 rgw，并绑定 80 端口 

复制

```shell
docker run -d \
        -p 80:80 \
        -v /etc/ceph:/etc/ceph \
        -v /var/lib/ceph/:/var/lib/ceph/ \
        ceph/daemon rgw
```

### 集群的最终状态

```
docker exec b79a02 ceph -s
    cluster 96ae62d2-2249-4173-9dee-3a7215cba51c
     health HEALTH_OK
     monmap e2: 1 mons at {ceph-admin=192.168.43.100:6789/0}
            election epoch 4, quorum 0 ceph-admin
     fsmap e5: 1/1/1 up {0=mds-ceph-admin=up:active}  
       mgr no daemons active 
     osdmap e136: 4 osds: 4 up, 4 in
            flags sortbitwise,require_jewel_osds,require_kraken_osds
      pgmap v1470: 136 pgs, 10 pools, 3782 bytes data, 223 objects
            254 MB used,  25301 MB / 25555 MB avail
                  136 active+clean

```

## 知乎

https://zhuanlan.zhihu.com/p/390377674