
class BaseAgaveflaskError(Exception):
    def __init__(self, msg=None, code=400):
        self.msg = msg
        self.code = code


class PermissionsError(BaseAgaveflaskError):
    """Error checking permissions or insufficient permissions needed to perform the action."""
    def __init__(self, msg=None, code=404):
        super(PermissionsError, self).__init__(msg=msg, code=code)


class DAOError(BaseAgaveflaskError):
    """General error accessing or serializing database objects."""
    pass


class ResourceError(BaseAgaveflaskError):
    """General error in the API resource layer."""
    pass