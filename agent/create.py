from prework import info
import os
from prework.precheck import precheck

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
