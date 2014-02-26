class ZTreeError(Exception):
    pass

class ContextPathError(ZTreeError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ConstraintError(ZTreeError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class QuantifierError(ConstraintError):
    def __init__(self, value):
        self.value = value

class SlugNotUniqueError(ZTreeError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class TreeFilterError(ZTreeError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
