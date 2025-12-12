class LTIError(Exception):
    pass


class LTIAuthenticationError(LTIError):
    pass


class LTIRequestError(LTIError):
    pass


class LTIConfigurationError(LTIError):
    pass
