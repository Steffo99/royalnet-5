class Config:
    def __init__(self,
                 name: str,
                 address: str,
                 port: int,
                 secret: str,
                 secure: bool = False,
                 path: str = "/"):
        if ":" in name:
            raise ValueError("Herald names cannot contain colons (:)")
        self.name = name

        self.address = address

        if port < 0 or port > 65535:
            raise ValueError("No such port")
        self.port = port

        self.secure = secure

        if ":" in secret:
            raise ValueError("Herald secrets cannot contain colons (:)")
        self.secret = secret

        if not path.startswith("/"):
            raise ValueError("Herald paths must start with a slash (/)")
        self.path = path

    @property
    def url(self):
        return f"ws{'s' if self.secure else ''}://{self.address}:{self.port}{self.path}"

    def __repr__(self):
        return f"<HeraldConfig for {self.url}>"
