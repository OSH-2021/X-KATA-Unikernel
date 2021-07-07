import info
import os

def create(name):
        '''
        创建虚拟机
        '''
        user = os.getenv('USER')

        conn = info.get_conn()
        f = open('domain.xml')
        xml = f.read()

        domain = conn.defineXML(xml.replace('$',name).replace('#',user))
        domain.create()
