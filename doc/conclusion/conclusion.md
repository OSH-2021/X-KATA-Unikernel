# 结题报告
- [1 项目简介](#1-项目简介)
- [2 背景和立项依据](#2-背景和立项依据)
  - [2.1 项目背景](#21-项目背景)
    - [2.1.1 传统容器的不足](#211-传统容器的不足)
    - [2.1.2 安全容器的提出](#212-安全容器的提出)
      - [gVisor的问题](#gvisor的问题)
      - [kata container 架构](#kata-container-架构)
        - [kata的虚拟化映射接口](#kata的虚拟化映射接口)
    - [2.1.3 Unikernel和虚拟机结合](#213-unikernel和虚拟机结合)
  - [2.2 立项依据](#22-立项依据)
    - [2.2.1 Unikernel选取](#221-unikernel选取)
    - [2.2.2 Unikernel的载体：KVM](#222-unikernel的载体kvm)
    - [2.2.3 对虚拟机进行管理：libvirt](#223-对虚拟机进行管理libvirt)
- [3 Kast 设计思路](#3-kast-设计思路)
  - [3.1 Kast整体架构](#31-kast整体架构)
  - [3.2 构建Images](#32-构建images)
    - [3.2.1 接收源码请求](#321 接收源码请求)
    - [3.2.2 构建img文件](#322-构建img文件)
      - [工具 ops](#工具-ops)
      - [分离build功能](#分离build功能)
  - [3.3 对libvirt API封装](#33-对libvirt-api封装)
    - [3.3.1 Libvirti API 所管理的主要对象](#331-libvirti-api-所管理的主要对象)
    - [3.3.2 主要API](#332-主要api)
      - [获取信息的API举例](#获取信息的api举例)
  - [3.4 虚拟机的可视化](#34-虚拟机的可视化)
- [4 成果演示](#4-成果演示)
  - [4.1 测试Golang和C++](#41-测试golang和c)
  - [4.2 简单对比](#42-简单对比)
  - [4.3 启动时间测量](#43-启动时间测量)
  - [4.4 运行时间测量](#44-运行时间测量)
  - [4.5 内存占用](#45-内存占用)
- [5 总结](#5-总结)
  - [5.1 项目特色](#51-项目特色)
  - [5.2 缺陷和前景](#52-缺陷和前景)
- [参考文献&资料](#参考文献资料)
## 1 项目简介

在云计算应用场景中，以Docker为代表的传统容器在遇到多租户场景时，它的安全问题立刻暴露了出来。 为此，先有kata container 提出安全容器的概念，用虚拟机弥补容器隔离的不足。然而其虚拟机过于重量级的问题，使得AWS对应推出了Firecracker microVM的方案，使得效率和资源消耗都有明显改善。而后有Google 提出的gVisor解决方案， 在容器的后端将所有的系统调用截断，凭借gVisor中用户程序来实现系统调用的API。 gVisor极其轻量，隔离性却也达到了操作系统能带来的隔离程度 。

两种思路都有各自的缺点，firecracker本质上还是传统的虚拟机架构，不可避免地带来多层嵌套的性能损耗。而gVisor 一是面临着隔离性不足的原生容器缺陷，二是面临着过多系统调用时无法忍受的上下文切换。

我们试图利用unikernel得天独厚的轻量和攻击面小的特性，结合虚拟化技术，为FaaS（Function As A Service）场景下的云服务提出一种解决方案：从客户端提交代码，到云平台进行Serverless运算。采用KVM 的虚拟机接口，在虚拟化环境中以unikernel减少资源开销，达到空间的高效利用和速度的极限提升。

## 2 背景和立项依据

### 2.1 项目背景

#### 2.1.1 传统容器的不足

传统容器使用 Namespace/Cgroup 实现，这套容器技术实际上同样是从进程调度的角度入手，对内核进行的功能扩展，优势上来说，操作界面很 Linux、很方便，开销也很低，可以被用来无负担地套在已有应用外面来构建隔离的环境，并且它是纯软件方案，不和其他层面的物理机、虚拟机相冲突。 

![docker structure](files\docker structure.png)

Namespace/Cgroup 是内核的一个部分，其中运行的容器仍然使用主机的 Linux 内核，他解决不了Linux内核中隔离性差的问题，攻击者可以利用Linux内核的漏洞来实施攻击，进而实现容器逃逸，然后便可以直接对宿主机进行攻击。 

#### 2.1.2 安全容器的提出

基于操作系统本身的容器机制没办法解决安全性问题，需要一个隔离层；而虚拟机是一个现成的隔离层，AWS这样的云服务已经让全世界相信，对用户来说，"secure of VM" 是可以满足需求的；虚拟机里面只要有个内核，就可以支持 OCI 规范的语义，在内核上跑个 Linux 应用这并不太难实现。

所以，安全容器的隔离层让应用的问题——不论是恶意攻击，还是意外错误——都不至于影响宿主机，也不会在不同的 Pod 之间相互影响。而且实际上，额外隔离层带来的影响并不仅是安全，对于调度、服务质量和应用信息的保护都有好处。

轻量内核的代表：unikernel 

安全容器的参考实现：kata-container 

轻量虚拟机的参考实现：Firecracker microVM

相关的实现有很多，我们这里只谈两个比较主流的实现：

- Kata Container 是MicroVM的一个经典的实现实现，它提供了一个MicroVM，并且有专门提供给 Kubernetes 使用的接口，有比较好的安全性和运行效率，现在已经开始逐步使用。但是其启动时间和内存占用与传统容器还有一定的差距。
- 而 gVisor 是基于进程虚拟化的容器实现，他拥有很好的隔离性，很小的内存占用和启动时间，但是系统调用效率不高，这是我们解决的重点问题。

##### gVisor的问题

![gVisor2](files\gVisor2.png)

gVisor 的大体结构是由 Sentry 和 Gofer 两个部分组成的。

Sentry 本身构成一个系统内核，对应用程序的一切系统调用做出回应，Sentry 所需要的一些系统功能由 Host Kernel 提供，但是 Sentry 只是用很小部分系统调用，有这样的保证呢，它就可以在内核和应用直接建立起了一层新的抽象。 Sentry 访问文件系统时，要通过 Gofer 进程处理，Gofer 进程可以使用完整的系统调用，但Sentry和Gofer使用严格的9P协议链接，有力的对不同组件进行解耦，防止不安全的系统调用。

一方面，gVisor 使用 Linux 提供的 ptrace 实现，ptrace 是一个用于调试进程的系统的调用，主要用于 gdb 以及 strace 这样的调试分析工具。不过 ptrace 系统调用非常强大，强大到 ptrace 可以支持这种将一个进程完全控制，捕获应用程序的所有系统调用和事件，但是 ptrace 在效率上有一定的问题。

应用程序在调用系统调用时，会进入内核态，然后内核会唤醒 Sentry 进程让 Sentry 进程执行，Sentry 进程执行完后，再进行一次系统调用切换到内核态，内核态继续转到应用程序中运行。

这样的过程中会出现大量的内核态到用户态的切换，这个过程中会出现大量的上下文切换。这个开销在以计算为主的应用比如深度学习环境下不是很大的问题，但它在需要使用大量系统调用的、这种IO密集型的服务端容器运行环境内是难以接受的，Xu Wang 和 Fupan Li 做了一组 benchmark，可以看到，gVisor 在 Nginx 上比 runC 和 Kata 慢了将近 50 倍。这个数据足以显示出 gVisor 的在系统调用密集的应用中性能与 Kata 和原本的 docker、runc 还是有较大差距。 

![gbenchmark](files\gbenchmark.png)

##### kata container 架构

![shimv2](files\shimv2.png)

`kata-agent` 负责启动容器进程，然后作为一个在虚拟机内守护进程，它使用ttRPC和host OS通信，shim-v2可以发送容器管理命令给agent，同时也可作为I/O stream的数据传输协议。

###### kata的虚拟化映射接口

上层接口：为了支持完整的CRI API 实现，kata需要提供以下结构

![img](files/api-to-construct.png)

下层接口：这些结构需要进一步被映射到和虚拟机交互的设备

![img](files/vm-concept-to-tech.png)

同样的，对轻量级的追求让kata的结构看起来仍然不够精简，于是，unikernel在保证完成功能的基础上，对内存的消耗和启动速度性能做了更进一步的优化。

#### 2.1.3 Unikernel和虚拟机结合

microVM的代表Firecracker，是在rust众多crates基础上实现的VMM，它拥有非常有限的设备模型，提供轻量级的服务并且暴露的攻击面极小，在FaaS场景下有极大的应用空间。不过，Firecracker 不支持文件系统分享，仅支持block-based 存储驱动。同时，它也不支持设备热插拔和VFIO。在安全容器的实现中，Kata Containers with Firecracker VMM 支持了CRI的一部分API，使得microVM的优点得以发挥。

Unikernel 与容器相比，虽然可以做的更小更安全，而且也不需要有 Docker Daemon 这样的后台程序存在，甚至不需要 Host OS，或者 Hypervisor，但是它一是与传统的软件过程有较大的出入，二是在分发等等方面不能做到像容器那样方便。所以它目前肯定不会成为主流的应用分发方式，还需要进一步探索。

综上，Unikernel的缺点可以被kata Container易于分发的优点改善，同时纳入kubernetes生态，使得Unikernel的应用更加广泛。我们的目标即能够完成虚拟机对Unikernel的封装，对资源占用和运行速度进一步优化。

![Unikernel](files\Unikernel.png)



### 2.2 立项依据

#### 2.2.1 Unikernel选取

![图片1](files\图片1.png)

Unikernel 是与某种语言紧密相关的，一种 unikernel 只能用一种语言写程序，这个LibraryOS 加上用户的程序最终被编译成一个操作系统，这个操作系统只跑专门的程序，里面也只有一个程序，没有其它冗余的程序，没有多进程切换，所以系统很小也很简单。

比如includeOS，只能运行c++的代码，这对于复杂的需求显然不能覆盖，如果针对一种或某种语言都要打包不同的Unikernel，那对虚拟机的要求则很难统一，维护和更新也变得十分困难。

Nanos 是一种新内核，旨在在虚拟化环境中运行一个且仅一个应用程序。 与 Windows 或 Linux 等通用操作系统相比，它有几个限制——即它是一个单进程系统，不支持运行多个程序，也没有用户或通过 ssh 进行远程管理的概念。

Nanos的最大特点是，可以覆盖到主流的Python，PHP，C++，Golang以及Rust等多种语言环境，使其通用性得到进一步扩展。

#### 2.2.2 Unikernel的载体：KVM

KVM全称是Kernel-based Virtual Machine，即基于内核的虚拟机，是采用硬件虚拟化技术的全虚拟化解决方案。

KVM最初是由Qumranet公司的Avi Kivity开发的，作为他们的VDI产品的后台虚拟化解决方案。为了简化开发，Avi Kivity并没有选择从底层开始新写一个Hypervisor，而是选择了基于Linux kernel，通过加载模块使Linux kernel本身变成一个Hypervisor。2006年10月，在先后完成了基本功能、动态迁移以及主要的性能优化之后，Qumranet正式对外宣布了KVM的诞生。同月，KVM模块的源代码被正式纳入Linux kernel，成为内核源代码的一部分。

![KVM](D:\GitHub\OS Big Lab\x-KATA-Unikernel\doc\conclusion\files\KVM.png)

**1.内存管理** KVM依赖Linux内核进行内存管理。上面提到，一个KVM客户机就是一个普通的Linux进程，所以，客户机的“物理内存”就是宿主机内核管理的普通进程的虚拟内存。进而，Linux内存管理的机制，如大页、KSM（Kernel Same Page Merge，内核的同页合并）、NUMA（Non-Uniform Memory Arch，非一致性内存架构）、通过mmap的进程间共享内存，统统可以应用到客户机内存管理上。

早期时候，客户机自身内存访问落实到真实的宿主机的物理内存的机制叫影子页表（Shadow Page Table）。KVM Hypervisor为每个客户机准备一份影子页表，与客户机自身页表建立一一对应的关系。客户机自身页表描述的是GVA→GPA的映射关系；影子页表描述的是GPA→HPA的映射关系。当客户机操作自身页表的时候，KVM就相应地更新影子页表。比如，当客户机第一次访问某个物理页的时候，由于Linux给进程的内存通常都是拖延到最后要访问的一刻才实际分配的，所以，此时影子页表中这个页表项是空的，KVM Hypervisor会像处理通常的缺页异常那样，把这个物理页补上，再返回客户机执行的上下文中，由客户机继续完成它的缺页异常。

影子页表的机制是比较拗口，执行的代价也是比较大的。所以，后来，这种靠软件的GVA→GPA→HVA→HPA的转换被硬件逻辑取代了，大大提高了执行效率。这就是Intel的EPT或者AMD的NPT技术，两家的方法类似，都是通过一组可以被硬件识别的数据结构，不用KVM建立并维护额外的影子页表，由硬件自动算出GPA→HPA。现在的KVM默认都打开了EPT/NPT功能。

**2.存储和客户机镜像的格式** 严格来说，这是QEMU的功能特性。

KVM能够使用Linux支持的任何存储来存储虚拟机镜像，包括具有IDE、SCSI和 SATA的本地磁盘，网络附加存储（NAS）（包括NFS和SAMBA/CIFS），或者支持iSCSI和光线通道的SAN。多路径I/O可用于改进存储吞吐量和提供冗余。

由于KVM是Linux内核的一部分，它可以利用所有领先存储供应商都支持的一种成熟且可靠的存储基础架构，它的存储堆栈在生产部署方面具有良好的记录。

KVM还支持全局文件系统（GFS2）等共享文件系统上的虚拟机镜像，以允许客户机镜像在多个宿主机之间共享或使用逻辑卷共享。磁盘镜像支持稀疏文件形式，支持通过仅在虚拟机需要时分配存储空间，而不是提前分配整个存储空间，这就提高了存储利用率。KVM 的原生磁盘格式为QCOW2，它支持快照，允许多级快照、压缩和加密。

**3.实时迁移** KVM支持实时迁移，这提供了在宿主机之间转移正在运行的客户机而不中断服务的能力。实时迁移对用户是透明的，客户机保持打开，网络连接保持活动，用户应用程序也持续运行，但客户机转移到了一个新的宿主机上。

除了实时迁移，KVM支持将客户机的当前状态（快照，snapshot）保存到磁盘，以允许存储并在以后恢复它。

**4.设备驱动程序** KVM支持混合虚拟化，其中半虚拟化的驱动程序安装在客户机操作系统中，允许虚拟机使用优化的 I/O 接口而不使用模拟的设备，从而为网络和块设备提供高性能的 I/O。

KVM 使用的半虚拟化的驱动程序是IBM和Redhat联合Linux社区开发的VirtIO标准；它是一个与Hypervisor独立的、构建设备驱动程序的接口，允许多种Hypervisor使用一组相同的设备驱动程序，能够实现更好的对客户机的互操作性。

同时，KVM也支持Intel的VT-d 技术，通过将宿主机的PCI总线上的设备透传（pass-through）给客户机，让客户机可以直接使用原生的驱动程序高效地使用这些设备。这种使用是几乎不需要Hypervisor的介入的。

**5.性能和可伸缩性** KVM也继承了Linux的性能和可伸缩性。KVM在CPU、内存、网络、磁盘等虚拟化性能上表现出色，大多都在原生系统的95%以上。KVM的伸缩性也非常好，支持拥有多达288个vCPU和4TB RAM的客户机，对于宿主机上可以同时运行的客户机数量，软件上无上限。

这意味着，任何要求非常苛刻的应用程序工作负载都可以运行在KVM虚拟机上。

下图说明，qemu-KVM是目前流行的对KVM调用的接口。

![qemukvm](\files\qemukvm.png)

>  有多种方法可以管理在 KVM 管理程序上运行的虚拟机 (VM)。例如，virt-manager 是一种流行的基于 GUI 的 VM 管理前端。但是，如果您想在无头服务器上使用 KVM，基于 GUI 的解决方案将不理想。事实上，您可以使用 kvm 命令行包装脚本完全从命令行创建和管理 KVM VM。或者，您可以使用 virsh，这是一个更易于使用的命令行用户界面，用于管理来宾 VM。在 virsh 之下，它与 libvirtd 服务通信，该服务可以控制多个不同的管理程序，包括 KVM、Xen、QEMU、LXC 和 OpenVZ。

> 当您希望自动配置和管理 VM 时，命令行管理界面（例如 virsh）也很有用。此外，virsh 支持多个管理程序的事实意味着您可以通过相同的 virsh 接口管理不同的管理程序。



#### 2.2.3 对虚拟机进行管理：libvirt

libvirt是一个管理虚拟化平台的工具包，可从 C、Python、Perl、Go 等语言访问 在开源许可下获得许可，并且支持 KVM、QEMU、Xen、Virtuozzo、VMWare ESX、LXC、BHyve 等。他针对 Linux、FreeBSD、Windows 和 macOS 被许多应用程序使用。

目前，libvirt 已经成为使用最为广泛的对各种虚拟机进行管理的工具和应用程序接口（API），而且一些常用的虚拟机管理工具（如virsh、virt-install、virt-manager等）和云计算框架平台（如OpenStack、OpenNebula、Eucalyptus等）都在底层使用libvirt的应用程序接口。 

![libvirt api](files\libvirt api.jpg)



## 3 Kast 设计思路

### 3.1 Kast整体架构

Kast里面核心的概念是`VirtManger`

![VirtManger](D:\GitHub\OS Big Lab\x-KATA-Unikernel\doc\conclusion\files\VirtManger.png)

### 3.2 构建Images

#### 3.2.1 接收源码请求

通过对后缀进行分类，根据参数相应地编译成二进制文件。再打包进镜像里。

#### 3.2.2 构建img文件

 ##### 工具 ops

ops是Nanos unikernel 的编译和编排工具。
大多数 Unikernel 专门用于高级语言，但 Nanos 能够执行任何有效的 ELF 二进制文件。 我们为常见的 linux 软件提供预先测试的软件包，包括对解释语言的支持，以提供类似 Linux 的体验。
该技术适用于 PHP、Node、Ruby、Lua、Perl 的软件包，并且正在开发中。 OPS 被明确构建为能够运行独立的静态二进制文件，例如 Go 和 C。

环境配置完毕后，对一个已有的执行

```shell
ops run main
```

便可以在ops自带的虚拟机上得到结果。

##### 分离build功能

由于我们需要在KVM上对虚拟机进行硬件加速，所以只需要构建内核这一步，对Ops的代码进行拆分，划分build模块。

具体是从命令行获取build指令

```go
func BuildCommand() *cobra.Command {
	var cmdBuild = &cobra.Command{
		Use:   "build [ELF file]",
		Short: "Build an image from ELF",
		Args:  cobra.MinimumNArgs(1),
		Run:   buildCommandHandler,
	}

	persistentFlags := cmdBuild.PersistentFlags()

	PersistConfigCommandFlags(persistentFlags)
	PersistBuildImageCommandFlags(persistentFlags)
	PersistProviderCommandFlags(persistentFlags)
	PersistNightlyCommandFlags(persistentFlags)
	PersistNanosVersionCommandFlags(persistentFlags)

	return cmdBuild
}
```

获取必要的内核配置信息

```go
p, ctx, err := getProviderAndContext(c, providerFlags.TargetCloud)

var imagePath string

if imagePath, err = p.BuildImage(ctx); err != nil {
	log.Fatal(err)
```

### 3.3 对libvirt API封装

#### 3.3.1 Libvirti API 所管理的主要对象

| 对象                    | 解释                                                         |
| ----------------------- | ------------------------------------------------------------ |
| Domain （域）           | 指运行在由Hypervisor提供的虚拟机器上的一个操作系统实例（常常是指一个虚拟机）或者用来启动虚机的配置。 |
| Hypervisor              | 一个虚拟化主机的软件层                                       |
| Node （主机）           | 一台物理服务器。                                             |
| Storage pool （存储池） | 一组存储媒介的集合，比如物理硬盘驱动器。一个存储池被划分为小的容器称作卷。卷会被分给一个或者多个虚机。 |
| Volume （卷）           | 一个从存储池分配的存储空间。一个卷会被分给一个或者多个域，常常成为域里的虚拟硬盘。 |

对应的图示如下：

![libvirt stru](D:\GitHub\OS Big Lab\x-KATA-Unikernel\doc\conclusion\files\libvirt stru.webp)

#### 3.3.2 主要API

```c
//开启、关闭域
int virDomainCreate         (virDomainPtr domain)//从持久性配置中引导并启动一个预先定义好的域
virDomainPtr    virDomainCreateLinux    (virConnectPtr conn, 
                     const char * xmlDesc, 
                     unsigned int flags)
#暂停\恢复\保存
int virDomainSuspend        (virDomainPtr domain)
int virDomainResume         (virDomainPtr domain)
int virDomainSave           (virDomainPtr domain, 
                     const char * to)
int virDomainRestore        (virConnectPtr conn, 
                     const char * from)
#销毁域
int virDomainDestroy        (virDomainPtr domain) 
```

##### 获取信息的API举例

```c
In [5]: print conn.getHostname()
ubuntu
In [8]: print conn.getMaxVcpus(None)
16
In [9]: print conn.getInfo()
['x86_64', 3934L, 8, 3591, 1, 2, 4, 1]
In [13]: print conn.getCellsFreeMemory(0,1)
[312676352L]

In [14]: print conn.getType()
QEMU

In [15]: print conn.getURI()
qemu:///system

In [16]: print conn.isEncrypted()
0

In [17]: print conn.isAlive()
1

In [18]: print conn.isSecure()
1

In [19]: print conn.getCPUMap()
(8, [True, True, True, True, True, True, True, True], 8

In [21]: print conn.getCPUStats(0)
{'kernel': 109650000000L, 'idle': 265725600000000L, 'user': 150740000000L, 'iowait': 26750000000L}
```

对于Unikernel，所需的XML文件并不复杂，关键的是<disk>标签

```xml
<disk type="file" device="disk">
      <driver name="qemu" type="raw"/>
      <source file="/home/#/.ops/images/$.img"/>
      <target dev="hda" bus="ide"/>
</disk>
```

以`qemu-kvm`接口建立对虚拟机的连接

```python
def get_conn():
        '''
        获取libvirt的连接句柄,用于提供操作libivrt的接口
        '''
        if is_virtual() == 'virt':
                try:
                        conn = libvirt.open('qemu:///system')
                except Exception as e:
                        sys.exit(e)
        return conn
```

对虚拟机的创建：

```python
def create(name):
        '''
        创建虚拟机
        '''
        precheck()

        os.system('ops build ' + name)

        user = os.getenv('USER')

        conn = info.get_conn()
        f = open('domain.xml')
        xml = f.read()

        domain = conn.defineXML(xml.replace('$',name).replace('#',user))
        domain.create()
```

### 3.4 虚拟机的可视化

`virt-viewer`是一个用于显示虚拟机的图形控制台的最小工具。 控制台使用VNC或SPICE访问协议。 可以基于其名称，ID或UUID来引用guest虚拟机。如果客户端尚未运行，则可以告知观看者请等待，直到它开始，然后尝试连接到控制台。此查看器可以连接到远程主机以查找控制台信息然后也使用同一网络连接到远程控制台。

比如对于一个ID为7的 qemu虚拟机：

```shell
 $ virt-viewer --connect qemu:///system 7
```

我们可以将结果重定向输出到主机，并转发给请求方

## 4 成果演示

### 4.1 测试Golang和C++

将经编译过的二进制文件`hello_world`传入

```shell
$ python3 main.py run hello_world
```

结果（C++同理）：

![hello](D:\GitHub\OS Big Lab\x-KATA-Unikernel\doc\conclusion\files\hello.png)

### 4.2 简单对比

![cmp](files\cmp.png)

### 4.3 启动时间测量

利用`qemu-boot-time`这个库， 使用 I/O 写入，我们可以跟踪固件和 Linux 内核中的事件。 

```shell
in trace_begin
sched__sched_process_exec     1 55061.435418353   289738 qemu-system-x86
kvm__kvm_entry           1 55061.466887708   289741 qemu-system-x86
kvm__kvm_pio             1 55061.467070650   289741 qemu-system-x86      rw=1, port=0xf5, size=1, count=1, val=1

kvm__kvm_pio             1 55061.475818073   289741 qemu-system-x86      rw=1, port=0xf5, size=1, count=1, val=4

kvm__kvm_pio             1 55061.477168037   289741 qemu-system-x86      rw=1, port=0xf4, size=1, count=1, val=3

kvm__kvm_pio             1 55061.558779540   289741 qemu-system-x86      rw=1, port=0xf4, size=1, count=1, val=5

kvm__kvm_pio             1 55061.686849663   289741 qemu-system-x86      rw=1, port=0xf4, size=1, count=1, val=6

in trace_end
Trace qemu-system-x86
pid 289738
qemu_init_end: 31.469355
fw_start: 31.652297 (+0.182942)
fw_do_boot: 32.39972 (+0.747423)
linux_start_boot: 33.749684 (+1.349964)
linux_start_kernel: 36.361187 (+2.611503)
```

如上，Unikernel在虚拟机中的启动时间为2.6s，令人满意。由于实际使用的情况也是在虚拟机中运行，所以不需要对bare metal进行测量。

### 4.4 运行时间测量

对一个大规模排序算法，尝试比较Unikernel和树莓派Linux的性能

![nanotime](D:\GitHub\OS Big Lab\x-KATA-Unikernel\doc\conclusion\files\nanotime.png)



![rasp](D:\GitHub\OS Big Lab\x-KATA-Unikernel\doc\conclusion\files\rasp.png)

值得注意的是，该树莓派缺少KVM的支持，同时不停需要等待硬件中断，所以时间消耗尤为不能忍受。

当我们切换为普通Linux版本执行该排序算法，所需时间消耗如下：

![1626009738387](files\normtime)

仍然比Unikernel要慢不少，这体现了Unikernel作为单进程系统的优越性。

### 4.5 内存占用

在分配虚拟机大小时，对于Unikernel分配了128MB空间，但对于树莓派Linux，即使分配了512MB也会返回错误信息，直到1GB才得以解决。这说明Unikernel对于存储资源的要求远远小于精简版Linux。

## 5 总结

### 5.1 项目特色

本次大作业致力于实现更为便捷轻量的Unikernel管理应用，并在这个过程中学习理解工业级代码，最终收获一个简易的虚拟机和Unikernel结合的实验性产品。

本次实验最大的难度在于Unikernel的迁移，虽然Unikernel的概念被提出很久，市面上也涌现很多Unikernel的具体实现，但要找到易于适配KVM，并且功能齐全的core，是一件比较困难的事情。本小组在调查资料的过程中偶然发现了 nanos，nanos 良好的可移植性深深地吸引了我们。我们也阅读了nanos的代码，加深了对系统架构的理解。

本项目另一个难度点在于没有统一的方式来方便地定义虚拟机相关的各种可管理对象。qemu-kvm 的命令行虚拟机管理工具参数众多，难于使用。不过好在libvirt的生态非常丰富，提供了virt-viewer和virt-install等工具大大减少了我们开发的难度

### 5.2 缺陷和前景

本项目在兼容性和功能完备性还有待改进，安全性还需要在实践中进一步检验。

计划中，与客户端的交互并未来得及完成，主要难点在于将虚拟机内部的结果重定向到主机，对结果的保护和加密是十分需要考虑的。而我们在这方面的积累太少，不足以支持我们做下去。

项目的前景非常光明，后续我们还可以将nanos进一步与firecracker结合，microVM与Unikernel的结合可以将性能发挥到极限。

## 参考文献&资料

[1]舒红梅,谭良.Unikernel的研究及其进展[J].计算机应用研究,2019,36(06):1601-1608.

[2]Pierre Olivier et al. A binary-compatible unikernel[C]. , 2019.

[3]Christine Hall. Kata Project Seeks to Improve Security with Virtualized Containers[J]. SQL Server Pro, 2018, 

[4]OpenStack Foundation; Kata Containers Project Launches to Build Secure Container Infrastructure[J]. Computer Weekly News, 2017,  : 165-.

[5]Serdar Yegulalp. What’s new in Kubernetes 1.20[J]. InfoWorld.com, 2020, 

[6]孔祥文,宋辰萱.基于Kubernetes的私有容器平台研究[J].电子技术与软件工程,2020(17):185-187.

[7]R. Kumar and B. Thangaraju, "Performance Analysis Between RunC and Kata Container Runtime," 2020 IEEE International Conference on Electronics, Computing and Communication Technologies (CONECCT), Bangalore, India, 2020, pp. 1-4, doi: 10.1109/CONECCT50063.2020.9198653.

[8]W. Viktorsson, C. Klein and J. Tordsson, "Security-Performance Trade-offs of Kubernetes Container Runtimes," 2020 28th International Symposium on Modeling, Analysis, and Simulation of Computer and Telecommunication Systems (MASCOTS), Nice, France, 2020, pp. 1-4, doi: 10.1109/MASCOTS50786.2020.9285946.

[9]J. Talbot et al., "A Security Perspective on Unikernels," 2020 International Conference on Cyber Security and Protection of Digital Services (Cyber Security), Dublin, Ireland, 2020, pp. 1-7, doi: 10.1109/CyberSecurity49315.2020.9138883.

[10]T. Goethals, M. Sebrechts, A. Atrey, B. Volckaert and F. De Turck, "Unikernels vs Containers: An In-Depth Benchmarking Study in the Context of Microservice Applications," 2018 IEEE 8th International Symposium on Cloud and Service Computing (SC2), Paris, France, 2018, pp. 1-8, doi: 10.1109/SC2.2018.00008.

[11]M. Yang and M. Huang, "An Microservices-Based Openstack Monitoring Tool," 2019 IEEE 10th International Conference on Software Engineering and Service Science (ICSESS), Beijing, China, 2019, pp. 706-709, doi: 10.1109/ICSESS47205.2019.9040740.

[12]D. Bernstein, "Containers and Cloud: From LXC to Docker to Kubernetes," in IEEE Cloud Computing, vol. 1, no. 3, pp. 81-84, Sept. 2014, doi: 10.1109/MCC.2014.51.

[13]V. Suryanarayana, K. Mylar Balasubramanya and R. Pendse, "Cache isolation and thin provisioning of hypervisor caches," 37th Annual IEEE Conference on Local Computer Networks, Clearwater Beach, FL, USA, 2012, pp. 240-243, doi: 10.1109/LCN.2012.6423618.

[14]E. Kim, K. Lee and C. Yoo, "On the Resource Management of Kubernetes," 2021 International Conference on Information Networking (ICOIN), Jeju Island, Korea (South), 2021, pp. 154-158, doi: 10.1109/ICOIN50884.2021.9333977.

[15 容器未来:AWS VS Google](https://zhuanlan.zhihu.com/p/55603422)

[16 OSH-2020 x-chital](https://github.com/OSH-2020/x-chital/blob/master/docs/research/research.md)

[17 Firecracker文档](https://firecracker-microvm.github.io/)

[18 gVisor文档](https://gvisor.dev/docs/)

[19 rust-vmm 开源项目](https://github.com/rust-vmm)

[20 NanoVMs Github主页](https://github.com/nanovms)

[21 libvirt官方文档](https://libvirt.org)

[22 VirtManager 主页](https://virt-manager.org)

[23 qemu-boot-time](https://github.com/stefano-garzarella/qemu-boot-time)

