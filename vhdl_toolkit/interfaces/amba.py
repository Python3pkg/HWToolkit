from vhdl_toolkit.synthetisator.interfaceLevel.interface import  Interface
from vhdl_toolkit.synthetisator.param import Param, shareAllParams
from vhdl_toolkit.interfaces.std import s, D
from vhdl_toolkit.hdlObjects.typeShortcuts import vecT, hInt


BURST_FIXED = 0b00
BURST_INCR = 0b01
BURST_WRAP = 0b10

BYTES_IN_TRANS_1 = 0b000
BYTES_IN_TRANS_2 = 0b001
BYTES_IN_TRANS_4 = 0b010
BYTES_IN_TRANS_8 = 0b011
BYTES_IN_TRANS_16 = 0b100
BYTES_IN_TRANS_32 = 0b101
BYTES_IN_TRANS_64 = 0b110
BYTES_IN_TRANS_128 = 0b111

CACHE_DEFAULT = 3
PROT_DEFAULT = 0
QOS_DEFAULT = 0
LOCK_DEFAULT = 0
RESP_OKAY = 0
RESP_EXOKAY = 1
RESP_SLVERR = 2
RESP_DECERR = 3

class AxiStream_withoutSTRB(Interface):
    DATA_WIDTH = Param(64)
    last = s(masterDir=D.OUT, alternativeNames=['tlast' ])
    data = s(masterDir=D.OUT, dtype=vecT(DATA_WIDTH), alternativeNames=['tdata' ])
    ready = s(masterDir=D.IN, alternativeNames=['tready' ])
    valid = s(masterDir=D.OUT, alternativeNames=['tvalid' ])

class AxiStream(AxiStream_withoutSTRB):
    strb = s(masterDir=D.OUT,
             dtype=vecT(AxiStream_withoutSTRB.DATA_WIDTH.opDiv(hInt(8))),
             alternativeNames=['tstrb', 'keep', 'tkeep' ])

class Axi_user(Interface):
    USER_WIDTH = Param(0)
    user = s(masterDir=D.OUT,
             dtype=vecT(USER_WIDTH),
             alternativeNames=['tuser'])   

class AxiStream_withUserAndNoStrb(AxiStream_withoutSTRB, Axi_user):
    pass
    
class AxiStream_withUserAndStrb(AxiStream, Axi_user):
    pass
    
class AxiLite_addr(Interface):
    ADDR_WIDTH = Param(32)
    addr = s(masterDir=D.OUT, dtype=vecT(ADDR_WIDTH), alternativeNames=['addr_v'])
    ready = s(masterDir=D.IN)
    valid = s(masterDir=D.OUT)

class AxiLite_r(Interface):
    DATA_WIDTH = Param(64)
    data = s(masterDir=D.IN, dtype=vecT(DATA_WIDTH), alternativeNames=['data_v'])
    resp = s(masterDir=D.IN, dtype=vecT(2), alternativeNames=['resp_v'])
    ready = s(masterDir=D.OUT)
    valid = s(masterDir=D.IN)

class AxiLite_w(Interface):
    DATA_WIDTH = Param(64)
    data = s(masterDir=D.OUT, dtype=vecT(DATA_WIDTH), alternativeNames=['data_v'])
    strb = s(masterDir=D.OUT,
             dtype=vecT(DATA_WIDTH.opDiv(hInt(8))), alternativeNames=['strb_v'])
    ready = s(masterDir=D.IN)
    valid = s(masterDir=D.OUT)
    
class AxiLite_b(Interface):
    resp = s(masterDir=D.IN, dtype=vecT(2), alternativeNames=['resp_v'])
    ready = s(masterDir=D.OUT)
    valid = s(masterDir=D.IN)

@shareAllParams    
class AxiLite(Interface):
    ADDR_WIDTH = Param(32)
    DATA_WIDTH = Param(64)
    aw = AxiLite_addr()
    ar = AxiLite_addr()
    w = AxiLite_w()
    r = AxiLite_r()
    b = AxiLite_b()

class AxiLite_addr_xil(AxiLite_addr):
    NAME_SEPARATOR = ''

class AxiLite_r_xil(AxiLite_r):
    NAME_SEPARATOR = ''

class AxiLite_w_xil(AxiLite_w):
    NAME_SEPARATOR = ''

class AxiLite_b_xil(AxiLite_b):
    NAME_SEPARATOR = ''
    
@shareAllParams   
class AxiLite_xil(AxiLite):
    aw = AxiLite_addr_xil()
    ar = AxiLite_addr_xil()
    w = AxiLite_w_xil()
    r = AxiLite_r_xil()
    b = AxiLite_b_xil()   

class Axi4_addr(AxiLite_addr):
    ID_WIDTH = Param(3)
    id = s(masterDir=D.OUT, dtype=vecT(ID_WIDTH), alternativeNames=['id_v'])
    burst = s(masterDir=D.OUT, dtype=vecT(2), alternativeNames=['burst_v'])
    cache = s(masterDir=D.OUT, dtype=vecT(4), alternativeNames=['cache_v'])
    len = s(masterDir=D.OUT, dtype=vecT(7), alternativeNames=['len_v'])
    lock = s(masterDir=D.OUT, dtype=vecT(2), alternativeNames=['lock_v'])
    prot = s(masterDir=D.OUT, dtype=vecT(3), alternativeNames=['prot_v'])
    size = s(masterDir=D.OUT, dtype=vecT(3), alternativeNames=['size_v'])
    qos = s(masterDir=D.OUT, dtype=vecT(4), alternativeNames=['qos_v'])


class Axi4_r(AxiLite_r):
    ID_WIDTH = Param(3)
    id = s(masterDir=D.IN, dtype=vecT(ID_WIDTH), alternativeNames=['id_v'])
    last = s(masterDir=D.IN)

class Axi4_w(AxiLite_w):
    ID_WIDTH = Param(3)
    id = s(masterDir=D.OUT, dtype=vecT(ID_WIDTH), alternativeNames=['id_v'])
    last = s(masterDir=D.OUT)
    
class Axi4_b(AxiLite_b):
    ID_WIDTH = Param(3)
    id = s(masterDir=D.IN, dtype=vecT(ID_WIDTH), alternativeNames=['id_v'])

@shareAllParams
class Axi4(AxiLite):
    ID_WIDTH = Param(3)
    aw = Axi4_addr()
    ar = Axi4_addr()
    w = Axi4_w()
    r = Axi4_r()
    b = Axi4_b()   

class Axi4_addr_xil(Axi4_addr):
    NAME_SEPARATOR = ''
class Axi4_r_xil(Axi4_r):
    NAME_SEPARATOR = ''
class Axi4_w_xil(Axi4_w):
    NAME_SEPARATOR = ''
class Axi4_b_xil(Axi4_b):
    NAME_SEPARATOR = ''


@shareAllParams
class Axi4_xil(Axi4):
    ar = Axi4_addr_xil()
    aw = Axi4_addr_xil()
    r = Axi4_r_xil()
    w = Axi4_w_xil()
    b = Axi4_b_xil()  
