class IPCConnectError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class IPCSendError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class ACKTimeoutError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class InvokeTimeoutError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class IPCInvokeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class IPCEventRequestError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
