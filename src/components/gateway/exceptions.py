class InvokeSessionTimeoutError(Exception):
    def __init__(self, request_id: str, appid: str | None, *args):
        super().__init__(*args)
        self.request_id = request_id
        self.appid = appid