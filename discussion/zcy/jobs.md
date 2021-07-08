# 背景：优势与改进空间

1. unikernal：
   - 提供更高的安全性
   - 比标准云应用占用更小的空间
   - 经过高度优化
   - 启动非常快
2. unikernal的缺点在于必须构建它们
3. kvm：软件虚拟化，配合qemu

# 开源软件

1. KVM和QEMU

    KVM是由Quramnet 开发，08年被RedHat收购，目前KVM由RedHat工程师开发维护，准确来说，KVM(Kernel-based Virtual Machine)只是一个linux内核模块，包括核心虚拟化模块kvm.ko，以及针对特定CPU的模块kvm-intel.ko或者kvm-amd.ko，其实现需要宿主机CPU支持硬件虚拟化
    
    而qemu本身就是一套完整的开源的全虚拟化解决方案，它有两种使用方式

    - 第一种是单独使用，对宿主机硬件没什么要求，也并不要求宿主机CPU支持虚拟化，qemu为虚拟机操作系统模拟整套硬件环境，虚拟机操作系统感觉不到自己运行在模拟的硬件环境中，这种纯软件模拟效率很低，但可以模拟出各种硬件设备，包括像软盘驱动器这样的老旧设备
    - 第二种是作为一个用户空间工具，和运行在内核中的KVM配合完成硬件环境的模拟，qemu1.3版本之前，其有一个专门的分支版本qemu-kvm作为KVM的用户空间程序(centos6.x yum源中就是这个)，qemu-kvm通过`ioctl`调用`/dev/kvm`这个接口与KVM交互，这样KVM在内核空间模拟虚拟机CPU，qemu-kvm负责模拟虚拟机I/O设备。qemu1.3及其以后版本中，qemu-kvm分支代码已经合并到qemu的master分支中，因此在qemu 1.3以上版本中，只需在编译qemu时开启`--enable-kvm`选项就能够是qemu支持kvm，具体说明可以查看[qemu官网](http://wiki.qemu.org/)
    
2. libvirt

    当启动虚拟机时，需要指定虚拟机的CPU，内存大小，使用的虚拟磁盘，网络使用NAT还是桥接方式，有几张网卡，磁盘等，这些复杂的配置参数需要有其它程序管理，所以Libvirt就登场了

    - libvirt是为了更方便地管理各种Hypervisor而设计的一套虚拟化库，libvirt作为中间适配层，让底层Hypervisor对上层用户空间的管理工具(virsh，virt-manager)做到完全透明，因为libvirt屏蔽了底层各种Hypervisor的细节，为上层管理工具提供了一个统一的、较稳定的接口（API）
    - 和手动使用qemu-kvm命令启动虚拟机不同，Libvirt使用xml文件来定义虚拟机的配置细节，就像上面提到的配置虚拟机CPU，内存大小，网络，磁盘这些都可以在xml文件中定义，然后使用这些定义启动虚拟机，所谓更改虚拟机配置，其实就是更改这个虚拟机的xml文件参数（更改某些参数需要重启虚拟机才会生效）
    
    
    
    3. nanos
    
       Nanos is a new kernel designed to run one and only one application in a virtualized environment.
    
       
    
    


# 基本实现方案

1. 对libvirt接口操作（virt-manager），实现a.将事先写好的xml文件读入给hypervisor，建立虚拟机，运行打包好的unikernal，b.通过命令行参数创建和修改xml文件，对虚拟机进行配置
2. 封装nanos（nanos-ops），实现 a.创建unikernal的img，b.读入config，批量创建image
3. 第二步的image通过网络传给第一步，将上述步骤作为单一操作（由client上传至server）


# 功能结构图
# 使用流程图

# 代码结构图