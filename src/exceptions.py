class APIException(Exception):
    def __init__(self, message):
        self.massage = message
        super().__init__(self.massage)


class HhAPIException(APIException):
    pass


class UserIneractionException(Exception):
    def __init__(self, message):
        self.massage = message
        super().__init__(self.massage)
