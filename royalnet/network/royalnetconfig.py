class RoyalnetConfig:
    def __init__(self,
                 master_uri: str,
                 master_secret: str):
        if not (master_uri.startswith("ws://")
                or master_uri.startswith("wss://")):
            raise ValueError("Invalid protocol (must be ws:// or wss://)")
        self.master_uri = master_uri
        self.master_secret = master_secret
