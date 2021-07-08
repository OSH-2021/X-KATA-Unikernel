from create import create
from prework import info
import opreat
import sys
import os
import virtms

cmds = ['create', 'list', 'destroy', 'suspend', 'reset', 
        'reboot', 'rename', 'shutdown', 'view', 'env', 
        'close', 'status']

def entrance():
    if len(sys.argv) <= 1:
        print('need argvs')
        return

    if sys.argv[1] not in cmds:
        print('Invalid command')
        return

    if sys.argv[1] == 'list':
        info.list()
        return

    elif sys.argv[1] == 'create':
        create(sys.argv[2])
        return

    elif sys.argv[1] == 'view':
        os.system('virt-viewer ' + sys.argv[2])
        return

    elif sys.argv[1] == 'destroy':
        opreat.destroy(sys.argv[2])
        return

    elif sys.argv[1] == 'shutdown':
        opreat.shutdown(sys.argv[2])
        return
    
    elif sys.argv[1] == 'rename':
        opreat.rename(sys.argv[2], sys.argv[3])
        return

    elif sys.argv[1] == 'status':
        print(virtms.get_status(sys.argv[2]))
        return
    
    elif sys.argv[1] == 'reboot':
        opreat.reboot(sys.argv[2])
        return
    
    elif sys.argv[1] == 'reset':
        opreat.reset(sys.argv[2])
        return
    
    elif sys.argv[1] == 'env':
        print('host name is: ' + info.get_hostname())
        print('max number of vcpus: ' + str(info.get_max_vcpus()))
        return   

    elif sys.argv[1] == 'close':
        info.close()
        return

    else:
        print('Invalid command')
        return help()

if __name__ == '__main__':
    entrance()
