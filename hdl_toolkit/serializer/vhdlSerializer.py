from hdl_toolkit.bitmask import Bitmask
from hdl_toolkit.hdlObjects.assignment import Assignment 
from hdl_toolkit.hdlObjects.operator import Operator
from hdl_toolkit.hdlObjects.operatorDefs import AllOps
from hdl_toolkit.hdlObjects.specialValues import Unconstrained
from hdl_toolkit.hdlObjects.statements import IfContainer, \
    SwitchContainer, WhileContainer, WaitStm
from hdl_toolkit.hdlObjects.types.array import Array
from hdl_toolkit.hdlObjects.types.bits import Bits
from hdl_toolkit.hdlObjects.types.defs import BOOL, BIT
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.hdlObjects.types.hdlType import HdlType, InvalidVHDLTypeExc
from hdl_toolkit.hdlObjects.types.typeCast import toHVal
from hdl_toolkit.hdlObjects.value import Value
from hdl_toolkit.serializer.exceptions import SerializerException
from hdl_toolkit.serializer.serializerClases.mapExpr import MapExpr
from hdl_toolkit.serializer.serializerClases.portMap import PortMap 
from hdl_toolkit.serializer.templates import VHDLTemplates
from hdl_toolkit.synthesizer.interfaceLevel.unitFromHdl import UnitFromHdl
from hdl_toolkit.synthesizer.param import getParam, Param
from hdl_toolkit.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hdl_toolkit.synthesizer.rtlLevel.signalUtils.exceptions import MultipleDriversExc
from python_toolkit.arrayQuery import arr_any, where


class VhdlVersion():
    v2002 = 2002
    v2008 = 2008

# keep in mind that there is no such a thing in vhdl itself
opPrecedence = {AllOps.NOT : 2,
                AllOps.EVENT: 1,
                AllOps.RISING_EDGE: 1,
                AllOps.DIV: 3,
                AllOps.ADD : 3,
                AllOps.SUB: 3,
                AllOps.MUL: 3,
                AllOps.MUL: 3,
                AllOps.XOR: 2,
                AllOps.EQ: 2,
                AllOps.NEQ: 2,
                AllOps.AND_LOG: 2,
                AllOps.OR_LOG: 2,
                AllOps.DOWNTO: 2,
                AllOps.GREATERTHAN: 2,
                AllOps.LOWERTHAN: 2,
                AllOps.CONCAT: 2,
                AllOps.INDEX: 1,
                AllOps.TERNARY: 1,
                AllOps.CALL: 1,
                }

class DoesNotContainsTernary(Exception):
    pass

def ternaryOpsToIf(statements):
    """Convert all ternary operators to IfContainers"""
    stms = []
    
    for st in statements:
        if isinstance(st, Assignment):
            try:
                if not isinstance(st.src, RtlSignalBase):
                    raise DoesNotContainsTernary()
                d = st.src.singleDriver()
                if not isinstance(d, Operator) or d.operator != AllOps.TERNARY:
                    raise DoesNotContainsTernary()
                else:
                    ifc = IfContainer(d.ops[0],
                                      [Assignment(d.ops[1], st.dst)]
                                      ,
                                      [Assignment(d.ops[2], st.dst)]
                           )
                    stms.append(ifc)
                
            except (MultipleDriversExc, DoesNotContainsTernary):
                stms.append(st)
        else:
            stms.append(st)
    return stms


class VhdlSerializer():
    VHDL_VER = VhdlVersion.v2002
    
    @classmethod
    def asHdl(cls, obj):
        if hasattr(obj, "asVhdl"):
            return obj.asVhdl(cls)
        elif isinstance(obj, UnitFromHdl):
            return str(obj)
        elif isinstance(obj, RtlSignalBase):
            return cls.SignalItem(obj)
        elif isinstance(obj, Value):
            return cls.Value(obj)
        else:
            try:
                serFn = getattr(cls, obj.__class__.__name__)
            except AttributeError:
                raise NotImplementedError("Not implemented for %s" % (repr(obj)))
            return serFn(obj)
    
    @classmethod
    def FunctionContainer(cls, fn):
        return  fn.name
    
    @classmethod
    def Architecture(cls, arch):
        variables = []
        procs = []
        extraTypes = set()
        for v in sorted(arch.variables, key=lambda x: x.name):
            variables.append(cls.SignalItem(v, declaration=True))
            if isinstance(v._dtype, (Enum, Array)):
                extraTypes.add(v._dtype)
        
        for p in sorted(arch.processes, key=lambda x: x.name):
            procs.append(cls.HWProcess(p))
            
             
        return VHDLTemplates.architecture.render({
        "entityName"         :arch.entityName,
        "name"               :arch.name,
        "variables"          :variables,
        "extraTypes"         :map(lambda typ: cls.HdlType(typ, declaration=True), extraTypes),
        "processes"          :procs,
        "components"         :map(cls.Component, arch.components),
        "componentInstances" :map(cls.ComponentInstance, arch.componentInstances)
        })
   
    @classmethod
    def Assignment(cls, a):
        if a.dst._dtype == a.src._dtype:
            return "%s <= %s" % (cls.asHdl(a.dst), cls.Value(a.src))
        else:
            raise SerializerException("%s <= %s  is not valid assignment because types are different(%s; %s) " % 
                             (cls.asHdl(a.dst), cls.Value(a.src), repr(a.dst._dtype), repr(a.src._dtype)))
    @classmethod
    def comment(cls, comentStr):
        return "--" + comentStr.replace("\n", "\n--")
    
    @classmethod
    def Component(cls, entity):
        return VHDLTemplates.component.render({
                "ports": [cls.PortItem(pi) for pi in entity.ports],
                "generics": [cls.GenericItem(g) for g in entity.generics],
                "entity": entity
                })      

    @classmethod
    def ComponentInstance(cls, entity):
        portMaps = []
        for pi in entity.ports:
            pm = PortMap.fromPortItem(pi)
            portMaps.append(pm)
        
        genericMaps = []
        for g in entity.generics:
            gm = MapExpr(g, g._val)
            genericMaps.append(gm) 
        
        if len(portMaps) == 0:
            raise Exception("Incomplete component instance")
        
        return VHDLTemplates.componentInstance.render({
                "instanceName" : entity._name,
                "entity": entity,
                "portMaps": [cls.PortConnection(x) for x in portMaps],
                "genericMaps" : [cls.MapExpr(x) for x in genericMaps]
                })     

    @classmethod
    def Entity(cls, ent):
        ent.ports.sort(key=lambda x: x.name)
        ent.generics.sort(key=lambda x: x.name)

        entVhdl = VHDLTemplates.entity.render({
                "name": ent.name,
                "ports" : [cls.PortItem(pi) for pi in ent.ports ],
                "generics" : [cls.GenericItem(g) for g in ent.generics]
                })

        doc = ent.__doc__
        if doc:
            doc = cls.comment(doc) + "\n"
            return doc + entVhdl   
        else:
            return entVhdl
    
    @classmethod
    def condAsHdl(cls, cond, forceBool):
        if isinstance(cond, RtlSignalBase):
            cond = [cond]
        else:
            cond = list(cond)
        if len(cond) == 1:
            c = cond[0]
            if not forceBool or c._dtype == BOOL:
                return cls.asHdl(c)
            elif c._dtype == BIT:
                return "(" + cls.asHdl(c) + ")='1'" 
            else:
                raise NotImplementedError()
            
        else:
            return " AND ".join(map(lambda x: cls.condAsHdl(x, forceBool), cond))
    
    @classmethod
    def IfContainer(cls, ifc):
        cond = cls.condAsHdl(ifc.cond, True)
        elIfs = []
        if cls.VHDL_VER < VhdlVersion.v2008:
            ifTrue = ternaryOpsToIf(ifc.ifTrue)
            ifFalse = ternaryOpsToIf(ifc.ifFalse)
        else:
            ifTrue = ifc.ifTrue
            ifFalse = ifc.ifFalse
        
        for c, statements in ifc.elIfs:
            if cls.VHDL_VER < VhdlVersion.v2008:
                statements = ternaryOpsToIf(statements)
                
            elIfs.append((cls.condAsHdl(c, True), statements))
        
        return VHDLTemplates.If.render(cond=cond,
                                       ifTrue=ifTrue,
                                       elIfs=elIfs,
                                       ifFalse=ifFalse)  
    @classmethod
    def SwitchContainer(cls, sw):
        switchOn = cls.condAsHdl(sw.switchOn, False)
        
        cases = []
        for key, statements in sw.cases:
            if key is not None:  # None is default
                key = cls.asHdl(key)
                
            if cls.VHDL_VER < VhdlVersion.v2008:
                statements = ternaryOpsToIf(statements)
                
            cases.append((key, statements))  
        return VHDLTemplates.Switch.render(switchOn=switchOn,
                                           cases=cases)  
    @classmethod
    def WaitStm(cls, w):
        if w.isTimeWait:
            return "wait for %d ns" % w.waitForWhat
        elif w.waitForWhat is None:
            return "wait"
        else:
            raise NotImplementedError()
        
        
    @classmethod
    def GenericItem(cls, g):
        s = "%s : %s" % (g.name, cls.HdlType(g._dtype))
        if g.defaultVal is None:
            return s
        else:  
            return  "%s := %s" % (s, cls.Value(getParam(g.defaultVal).staticEval()))
    
    @classmethod
    def PortConnection(cls, pc):
        if pc.portItem._dtype != pc.sig._dtype:
            raise SerializerException("Port map %s is nod valid (types does not match)  (%s, %s)" % (
                      "%s => %s" % (pc.portItem.name, cls.asHdl(pc.sig)),
                      repr(pc.portItem._dtype), repr(pc.sig._dtype)))
        return " %s => %s" % (pc.portItem.name, cls.asHdl(pc.sig))      
    
    @classmethod
    def PortItem(cls, pi):
        try:
            return "%s : %s %s" % (pi.name, pi.direction,
                                   cls.HdlType(pi._dtype))
        except InvalidVHDLTypeExc as e:
            e.variable = pi
            raise e

    @staticmethod
    def BitString_binary(v, width, vldMask=None):
        buff = []
        for i in range(width - 1, -1, -1):
            mask = (1 << i)
            b = v & mask
            
            if vldMask & mask:
                s = "1" if b else "0"
            else:
                s = "X"
            buff.append(s)
        return '"%s"' % (''.join(buff))

    @classmethod
    def BitString(cls, v, width, vldMask=None):
        if vldMask is None:
            vldMask = width
        # if can be in hex
        if width % 4 == 0 and vldMask == (1 << width) - 1:
            return ('X"%0' + str(width // 4) + 'x"') % (v)
        else:  # else in binary
            return cls.BitString_binary(v, width, vldMask)
    
    @classmethod
    def BitLiteral(cls, v, vldMask):
        if vldMask:
            return  "'%d'" % int(bool(v))
        else:
            return "'X'"
    
    @classmethod
    def SignedBitString(cls, v, width, vldMask):
        if vldMask != Bitmask.mask(width):
            raise SerializerException(
            "Value %s can not be serialized as signed bit string literal due not all bits are valid" % 
             repr(v))
        else:
            # [TODO] parametrized width
            return "TO_SIGNED(%d, %d)" % (v, width)

    @classmethod
    def UnsignedBitString(cls, v, width, vldMask):
        if vldMask != Bitmask.mask(width):
            raise SerializerException(
            "Value %s can not be serialized as signed bit string literal due not all bits are valid" % 
             repr(v))
        else:
            # [TODO] parametrized width
            return "TO_UNSIGNED(%d, %d)" % (v, width)
    
    @classmethod
    def SignalItem(cls, si, declaration=False):
        if declaration:
            if si.drivers:
                prefix = "SIGNAL"
            elif si.endpoints or si.simSensitiveProcesses:
                prefix = "CONSTANT"
            else:
                raise SerializerException("Signal %s should be declared but it is not used" % si.name)
                

            s = prefix + " %s : %s" % (si.name, cls.HdlType(si._dtype))
            if si.defaultVal is not None:
                v = si.defaultVal
                if isinstance(v, RtlSignalBase):
                    return s + " := %s" % cls.asHdl(v)
                elif isinstance(v, Value):
                    if si.defaultVal.vldMask:
                        return s + " := %s" % cls.Value(si.defaultVal)
                else:
                    raise NotImplementedError(v)
                
            return s 
        else:
            if si.hidden and hasattr(si, "origin"):
                return cls.asHdl(si.origin)
            else:
                return si.name

    @staticmethod
    def VHDLExtraType(exTyp):
        return "TYPE %s IS (%s);" % (exTyp.name, ", ".join(exTyp.values))
    
    @classmethod
    def VHDLGeneric(cls, g):
        t = cls.HdlType(g._dtype)
        if hasattr(g, "defaultVal"):
            return "%s : %s := %s" % (g.name, t,
                                      cls.Value(g, g.defaultVal))
        else:
            return "%s : %s" % (g.name, t)

    @classmethod
    def HdlType_bits(cls, typ, declaration=False):
        disableRange = False
        if typ.signed is None:
            if typ.forceVector or typ.bit_length() > 1:
                name = 'STD_LOGIC_VECTOR'
            else:
                name = 'STD_LOGIC'
                disableRange = True
        elif typ.signed:
            name = "SIGNED"
        else:
            name = 'UNSIGNED'     
            
        c = typ.constrain
        if disableRange or c is None or isinstance(c, Unconstrained):
            constr = ""
        elif isinstance(c, (int, float)):
            constr = "(%d DOWNTO 0)" % (c-1)
        else:        
            constr = "(%s)" % cls.Value(c)     
        return name + constr

    @classmethod
    def HdlType_enum(cls, typ, declaration=False):
        buff = []
        if declaration:
            buff.extend(["TYPE ", typ.name.upper(), ' IS ('])
            buff.append(", ".join(typ._allValues))
            buff.append(")")
        else:
            return typ.name
        return "".join(buff)

    @classmethod
    def HdlType_array(cls, typ, declaration=False):
        name = "arrT_%d" % (id(typ))
        if declaration:
            return "TYPE %s IS ARRAY ((%s) DOWNTO 0) OF %s" % \
                (name, cls.asHdl(toHVal(typ.size) - 1), cls.HdlType(typ.elmType))
        else:
            return name

    @classmethod
    def HdlType(cls, typ, declaration=False):
        assert isinstance(typ, HdlType)
        if isinstance(typ, Bits):
            return cls.HdlType_bits(typ, declaration=declaration)
        elif isinstance(typ, Enum):
            return cls.HdlType_enum(typ, declaration=declaration)
        elif isinstance(typ, Array):
            return cls.HdlType_array(typ, declaration=declaration)
        else:
            if declaration:
                raise NotImplementedError("type declaration is not impleneted for type %s" % 
                                      (typ.name))
            else:
                return typ.name.upper()
                
    @classmethod
    def VHDLVariable(cls, v):
        prefix = "VARIABLE"
        s = prefix + " %s : %s" % (v.name, cls.HdlType(v._dtype))
        if v.defaultVal is not None:
            return s + " := %s" % cls.Value(v, v.defaultVal)
        else:
            return s
                
    @classmethod
    def HWProcess(cls, proc):
        body = proc.statements
        hasToBeVhdlProcess = arr_any(body, lambda x: isinstance(x, 
                                        (IfContainer, SwitchContainer, WhileContainer, WaitStm)))
        sensitifityList = list(where(proc.sensitivityList, lambda x : not isinstance(x, Param)))
        return VHDLTemplates.process.render({
              "name": proc.name,
              "hasToBeVhdlProcess": hasToBeVhdlProcess,
              "sensitivityList": ", ".join([cls.asHdl(s) for s in sensitifityList]),
              "statements": [ cls.asHdl(s) for s in body] })
    
    @classmethod
    def MapExpr(cls, m):
        return   "%s => %s" % (m.compSig.name, cls.asHdl(m.value))
    
    @classmethod
    def Value(cls, val):
        """ 
        @param dst: is VHDLvariable connected with value 
        @param val: value object, can be instance of Signal or Value    """
        if isinstance(val, Value):
            return val._dtype.valAsVhdl(val, cls)
        elif isinstance(val, RtlSignalBase):
            return cls.SignalItem(val)
        else:
            raise Exception("value2vhdlformat can not resolve value serialization for %s" % (repr(val))) 
        
    @classmethod
    def BitToBool(cls, cast):
        v = 0 if cast.sig.negated else 1
        return cls.asHdl(cast.sig) + "=='%d'" % v

    @classmethod
    def Operator(cls, op):
        def p(operand):
            s = cls.asHdl(operand)
            if isinstance(operand, RtlSignalBase):
                try:
                    o = operand.singleDriver()
                    if opPrecedence[o.operator] <= opPrecedence[op.operator]:
                        return " (%s) " % s
                except Exception:
                    pass
            return " %s " % s
        
        ops = op.ops
        o = op.operator
        def _bin(name):
            return (" " + name + " ").join(map(lambda x: x.strip(), map(p, ops)))
        
        if o == AllOps.AND_LOG:
            return _bin('AND')
        elif o == AllOps.OR_LOG:
            return _bin('OR')
        elif o == AllOps.XOR:
            return _bin('XOR')
        elif o == AllOps.NOT:
            assert len(ops) == 1
            return "NOT " + p(ops[0])
        elif o == AllOps.CALL:
            return "%s(%s)" % (cls.FunctionContainer(ops[0]), ", ".join(map(p, ops[1:])))
        elif o == AllOps.CONCAT:
            return _bin('&')
        elif o == AllOps.DIV:
            return _bin('/')
        elif o == AllOps.DOWNTO:
            return _bin('DOWNTO')
        elif o == AllOps.EQ:
            return _bin('=')
        elif o == AllOps.EVENT:
            assert len(ops) == 1
            return p(ops[0]) + "'EVENT"
        elif o == AllOps.GREATERTHAN:
            return _bin('>')
        elif o == AllOps.GE:
            return _bin('>=')
        elif o == AllOps.LE:
            return _bin('<=')
        elif o == AllOps.INDEX:
            assert len(ops) == 2
            return "%s(%s)" % ((cls.asHdl(ops[0])).strip(), p(ops[1]))
        elif o == AllOps.LOWERTHAN:
            return _bin('<')
        elif o == AllOps.SUB:
            return _bin('-')
        elif o == AllOps.MUL:
            return _bin('*')
        elif o == AllOps.NEQ:
            return _bin('/=')
        elif o == AllOps.ADD:
            return _bin('+')
        elif o == AllOps.TERNARY:
            return p(ops[1]) + " WHEN " + cls.condAsHdl([ops[0]], True) + " ELSE " + p(ops[2])
        elif o == AllOps.RISING_EDGE:
            assert len(ops) == 1
            return "RISING_EDGE(" + p(ops[0]) + ")"
        elif o == AllOps.FALLIGN_EDGE:
            assert len(ops) == 1
            return "FALLING_EDGE(" + p(ops[0]) + ")"
        elif o == AllOps.BitsAsSigned:
            assert len(ops) == 1
            return  "SIGNED(" + p(ops[0]) + ")"
        elif o == AllOps.BitsAsUnsigned:
            assert len(ops) == 1
            return  "UNSIGNED(" + p(ops[0]) + ")"
        elif o == AllOps.BitsAsVec:
            assert len(ops) == 1
            return  "STD_LOGIC_VECTOR(" + p(ops[0]) + ")"
        elif o == AllOps.BitsToInt:
            assert len(ops) == 1
            op = cls.asHdl(ops[0])
            if ops[0]._dtype.signed is None:
                op = "UNSIGNED(%s)" % op
            return "TO_INTEGER(%s)" % op
        elif o == AllOps.IntToBits:
            assert len(ops) == 1
            resT = op.result._dtype
            op_str = cls.asHdl(ops[0])
            w = resT.bit_length()
            
            if resT.signed is None:
                return "STD_LOGIC_VECTOR(TO_UNSIGNED(" + op_str + ", %d))" % (w)
            elif resT.signed:
                return "TO_UNSIGNED(" + op_str + ", %d)" % (w)
            else:
                return "TO_UNSIGNED(" + op_str + ", %d)" % (w)
            
        elif o == AllOps.POW:
            assert len(ops) == 2
            return _bin('**')
        else:
            raise NotImplementedError("Do not know how to convert %s to vhdl" % (o))

