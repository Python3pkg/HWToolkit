
class HdlSimConfig():
    """
    Container of configuration of hdl simulator
    """
    def __init__(self):
        # set to None to prevent redundant calls
        self.beforeSim = None
        self.logChange = None
        self.logPropagation = None
        self.logApplyingValues = None

    def beforeSim(self, simulator, synthesisedUnit):
        """
        called beforee preparing of simulation
        """
        pass

    def logChange(self, nowTime, sig, nextVal):
        """
        Log change of value for signal
        """
        pass

    def logPropagation(self, simulator, signal, process):
        """
        Log value propagation over netlist
        """
        pass

    def logApplyingValues(self, simulator, values):
        """
        Log simulator value quantum applied
        """
        pass
