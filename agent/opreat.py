from prework import info
import os

def destroy(name):
        '''
        销毁虚拟机
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(name)
        dom.destroy()
        return

def rename(old_name, new_name):
        '''
        重命名虚拟机
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(old_name)
        dom.rename(new_name)
        return

def reboot(name):
        '''
        重启虚拟机
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(name)
        dom.reboot()
        return

def reset(name):
        '''
        重置虚拟机
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(name)
        dom.reset()
        return

def suspend(name):
        '''
        暂停虚拟机
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(name)
        dom.suspend()
        return

def shutdown(name):
        '''
        关闭虚拟机
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(name)
        dom.shutdown()
        return
