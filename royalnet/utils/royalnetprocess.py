from typing import *
import dataclasses
import multiprocessing


@dataclasses.dataclass()
class RoyalnetProcess:
    constructor: Callable[[], multiprocessing.Process]
    current_process: Optional[multiprocessing.Process]
