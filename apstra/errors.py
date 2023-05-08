import http.client

class ErrorApstraAPI(Exception):
    """
    Error Exception class for handling Apstra API errors
    """
    def __init__(self, message: str, code: http.HTTPStatus = None):
        self.message = message
        self.code = code
        self.codemap = {}
        
        if self.code is not None:
            self.codemap = {k:v for k,v in http.client.responses.items() if k <= self.code} or {self.code: http.client.responses[http.client.INTERNAL_SERVER_ERROR]}
            super().__init__(f"{self.code} {self.codemap[self.code]}: {self.message}")
        else:
            super().__init__(self.message)