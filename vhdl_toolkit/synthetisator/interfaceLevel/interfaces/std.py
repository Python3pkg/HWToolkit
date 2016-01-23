from vhdl_toolkit.synthetisator.interfaceLevel.interface import  Interface
from vhdl_toolkit.types import DIRECTION
from vhdl_toolkit.synthetisator.param import Param

D = DIRECTION

class Ap_none(Interface):
    _baseName = ''
    def __init__(self, *destinations, masterDir=DIRECTION.OUT, width=1, src=None, \
                  isExtern=False, alternativeNames=None):
        Interface.__init__(self, *destinations, masterDir=masterDir, src=src, \
                           isExtern=isExtern, alternativeNames=alternativeNames)
        self._width = width

s = Ap_none        

class Ap_clk(Ap_none):
    _baseName = 'ap_clk'

class Ap_rst_n(Ap_none):
    _baseName = 'ap_rst_n'
    
class Ap_hs(Interface):
    DATA_WIDTH = Param(64)
    data = s(width=DATA_WIDTH)
    rd = s(masterDir=D.IN)
    vld = s()

class BramPort_withoutClk(Interface):
    ADDR_WIDTH = Param(32)
    DATA_WIDTH = Param(64) 
    addr = s(width=ADDR_WIDTH, alternativeNames=['addr_v'])
    din = s(width=DATA_WIDTH, alternativeNames=['din_v'])
    dout = s(masterDir=D.IN, width=DATA_WIDTH, alternativeNames=['dout_v'])
    en = s()
    we = s()   

class BramPort(BramPort_withoutClk):
    clk = s(masterDir=D.OUT)


class SPI(Interface):
    clk = Ap_clk()
    mosi = Ap_none()
    miso = Ap_none(masterDir=D.IN)
    ss = Ap_none()
  
class RGMII_channel(Interface):
    DATA_WIDTH = 4
    c = s()
    d = s(width=DATA_WIDTH)
    x_ctl = s()
    