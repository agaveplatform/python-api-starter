
class BaseAgaveflaskError(Exception):
    def __init__(self, msg=None):
        self.msg = msg


class PermissionsError(BaseAgaveflaskError):
    """Error checking permissions or insufficient permissions needed to perform the action."""
    pass


class DAOError(BaseAgaveflaskError):
    """General error accessing or serializing database objects."""
    pass


class ResourceError(BaseAgaveflaskError):
    """General error in the API resource layer."""
    pass