import info
import os

def get_status(name):
        '''
        查看当前虚拟机状态
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(name)
        return dom.info()

def get_vpus(name):
        '''
        查看当前虚拟机cpus数
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(name)
        return dom.vcpus()

def get_memory(name):
        '''
        查看当前虚拟机最大的memory
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(name)
        return dom.maxMemory()

def sreen(name):
        '''
        获取屏幕截图
        '''
        conn = info.get_conn()
        dom = conn.lookupByName(name)
        stream = conn.newStream()
        return dom.screenshot(stream,0)
