class SysLog:
    def __init__(self,logfile=None):
        self.log = []
        self.callbacks = []
        self.logfile = None
        if logfile:
            self.logfile = open(logfile,"w")
            self.callbacks.append(self.logfile_write)
    def add_callback(self,f):
        self.callbacks.append(f)
    def write(self,*message):
        s = "> "+"".join(str(x) for x in message)
        self.log.append(s)
        [f(s) for f in self.callbacks]
    def logfile_write(self,s):
        self.logfile.write(s+"\n")
        self.logfile.flush()
    def read(self):
        return "\n".join(self.log)