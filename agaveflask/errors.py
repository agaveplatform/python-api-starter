
class BaseAgaveflaskError(Exception):
    def __init__(self, msg=None):
        self.msg = msg

class PermissionsError(BaseAgaveflaskError):
    pass

