class Flavor:
    def __init__(
        self,
        cpu: str="0",
        memory: str="0",
        disk: str="0",
        gpu: str="0",
        gpu_type: str=None
    ):
        self.cpu = cpu
        self.memory = memory
        self.disk = disk
        self.gpu = gpu
        self.gpu_type = gpu_type