import sys
try:
        import libvirt
        HAS_LIBVIRT = True
except Exception:
        HAS_LIBVIRT = False
def is_virtual():
        '''
        判断当前系统是否支持KVM虚拟化,不支持则退出
        '''
        if not HAS_LIBVIRT:
                sys.exit("current system are not support Virtualization")
        return 'virt' 
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
def close_conn(conn):
        '''
        关闭libvirt的连接句柄
        '''
        return conn.close()
def list_active_vms():
        '''
        获取所有开机状态的instance,返回虚拟机的名字
        '''
        vms_list = []
        conn = get_conn()
        domain_list = conn.listDomainsID()
        for id in domain_list:
                vms_list.append(conn.lookupByID(id).name())
        close_conn(conn)
        return vms_list
def list_inactive_vms():
        '''
        获取关机状态的instance，返回虚拟机的名字
        '''
        vms_list = []
        conn = get_conn()
        for id in conn.listDefinedDomains():
                vms_list.append(id)
        close_conn(conn)
        return vms_list
def list_all_vms():
        '''
        获取所有的虚拟机
        '''
        vms = []
        vms.extend(list_active_vms())
        vms.extend(list_inactive_vms())
        return vms
def get_capability():
        '''
        得到hypervisor的容量信息,返回格式为XML
        '''
        conn = get_conn()
        capability = conn.getCapabilities()
        conn.close()
        return capability
def get_hostname():
        '''
        attain hypervisor's hostname
        '''
        conn = get_conn()
        hostname = conn.getHostname()
        conn.close()
        return hostname
def get_max_vcpus():
        '''
        获取hypervisor支持虚拟机的最大CPU数
        '''
        conn = get_conn()
        max_vcpus = conn.getMaxVcpus(None)
        conn.close()
        return max_vcpus
