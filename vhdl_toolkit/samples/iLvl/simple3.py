from vhdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from vhdl_toolkit.interfaces.std import Ap_none
from vhdl_toolkit.formater import formatVhdl
from vhdl_toolkit.synthetisator.param import Param
from vhdl_toolkit.hdlObjects.typeShortcuts import vecT



class SimpleUnit3(Unit):
    DATA_WIDTH = Param(8)
    a = Ap_none(dtype=vecT(DATA_WIDTH), isExtern=True)
    b = Ap_none(dtype=vecT(DATA_WIDTH), src=a, isExtern=True)


if __name__ == "__main__":
    u = SimpleUnit3()
    print(formatVhdl(
                     "\n".join([ str(x) for x in u._synthesise()])
                     ))