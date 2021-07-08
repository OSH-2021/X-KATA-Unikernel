import os

def precheck():
    vcpus = os.popen('grep -Eoc \'(vmx|svm)\' /proc/cpuinfo') 
    if vcpus.read() == 0:
        print('your cpu doesnot support virtualization')
        exit(-1)

    guard = os.popen('systemctl is-active libvirtd')
    if guard.read() != 'active\n':
        print('the guard programm for libvirt has not started')
        exit(-1)

    ops = os.popen('ops version')
    if ops.read()[0:11] != 'Ops version':
        print('the unikernel of nanos not exist')
        exit(-1)