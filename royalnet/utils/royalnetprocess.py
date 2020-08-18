import dataclasses
import multiprocessing
from typing import *


@dataclasses.dataclass()
class RoyalnetProcess:
    constructor: Callable[[], multiprocessing.Process]
    current_process: Optional[multiprocessing.Process]
