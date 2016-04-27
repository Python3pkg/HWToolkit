from hdl_toolkit.synthetisator.rtlLevel.codeOp import IfContainer
from hdl_toolkit.hdlObjects.operatorDefs import AllOps


class DepContainer():
    def __init__(self):
        self.pos = set()  # if cond
        self.neg = set()  # if not cond
        
    def __repr__(self):
        return "<DepContainer pos:%s, neg:%s>" % (repr(self.pos), repr(self.neg))

class IfTreeNode():
    def __init__(self):
        self.posSt = []
        self.pos = {}
        self.negSt = []
        self.neg = {}

def renderIfTree(assigments):
    termMap = {}

    def insertToMap(condSig, assigment, isNegated):
        try:
            cont = termMap[condSig]
        except KeyError:
            cont = DepContainer()
            termMap[condSig] = cont
        if isNegated:
            cont.neg.add(assigment)
        else:
            cont.pos.add(assigment)
    
    def getBaseCond(c):
        """
        if is negated return original cond and negated flag
        """
        isNegated = False
        drivers = []
        try:
            drivers = c.drivers
        except AttributeError:
            pass
        if len(drivers) == 1:
            d = list(c.drivers)[0]
            if d.operator == AllOps.NOT:
                c = d.ops[0]
                isNegated = True
        return (c, isNegated)
    
    def registerToMap(assigment):
        for c in assigment.cond:
            realC, isNegated = getBaseCond(c)
            insertToMap(realC, assigment, isNegated)
                
    def countCondOccurrences(termMap):
        """inf means it is event dependent cond and it should be used as highest priority cond"""
        for cond, container in termMap.items():
            drivers = None
            try:
                drivers = cond.drivers
            except AttributeError:
                pass
            
            if drivers is not None and len(drivers) == 1 \
               and list(drivers)[0].operator == AllOps.RISING_EDGE:
                cnt = float('inf')
            else:
                cnt = len(container.pos) + len(container.neg)
            yield (cond, cnt)
    
    def sortCondsByMostImpact(countedConds):
        for c in sorted(countedConds, key=lambda x: x[1]):
            yield c[0]
   
    # resolve main hierarchy of conditions
    for a in assigments:
        registerToMap(a)
    
    condOrder = list(sortCondsByMostImpact(countCondOccurrences(termMap)))

    top = IfTreeNode()
    
    def toTree():
        """register assigments in tree of IfTreeNodes"""
        for a in assigments:
            _top = top.pos
            topNode = top
            # buld cond path in node tree
            realCond = [ getBaseCond(c) for c in a.cond ]
            sortedCond = sorted(realCond,
                                key=lambda x: condOrder.index(x[0]),
                                reverse=True)
            isNegated = False

            # walk cond path in node tree
            for c, isNegated in sortedCond:
                try:
                    _top = _top[c]
                except KeyError:
                    t = IfTreeNode()
                    _top[c] = t
                    _top = t
                    
                topNode = _top
                if isNegated:
                    _top = _top.neg
                else:
                    _top = _top.pos
                    
            # register this assigment at the end of cond path        
            if isNegated:
                topNode.negSt.append(a)
            else:
                topNode.posSt.append(a)
    toTree()

    def _renderIfTree(cond, node):
        """
        Render tree of IfTreeNode objects
        """
        ifTrue = []
        ifFalse = []
        
        def __renderIfTree(statements, subIfs, resultContainer):
            for st in statements:
                resultContainer.append(st)
            for k, v in subIfs.items():
                for o in _renderIfTree(k, v): 
                    resultContainer.append(o)
                
        __renderIfTree(node.posSt, node.pos, ifTrue)
        __renderIfTree(node.negSt, node.neg, ifFalse)
        ic = IfContainer([cond], ifTrue, ifFalse)
        yield ic
        
    if condOrder:
        for k, v in top.pos.items():
            yield from _renderIfTree(k, v)
    else:
        # none of assignments has condition
        yield from assigments