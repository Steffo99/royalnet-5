from typing import Optional


class Config:
    def __init__(self,
                 name: str,
                 address: str,
                 port: int,
                 secret: str,
                 secure: bool = False,
                 path: str = "/"
                 ):
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

    def copy(self,
             name: Optional[str] = None,
             address: Optional[str] = None,
             port: Optional[int] = None,
             secret: Optional[str] = None,
             secure: Optional[bool] = None,
             path: Optional[str] = None):
        """Create an exact copy of this configuration, but with different parameters."""
        return self.__class__(name=name if name else self.name,
                              address=address if address else self.address,
                              port=port if port else self.port,
                              secret=secret if secret else self.secret,
                              secure=secure if secure else self.secure,
                              path=path if path else self.path)

    def __repr__(self):
        return f"<HeraldConfig for {self.url}>"

    @classmethod
    def from_config(cls, *,
                    name: str,
                    address: str,
                    port: int,
                    secret: str,
                    secure: bool = False,
                    path: str = "/",
                    enabled: ... = ...
                    ):
        return cls(
            name=name,
            address=address,
            port=port,
            secret=secret,
            secure=secure,
            path=path
        )
