import typing
from sqlalchemy.inspection import inspect


def relationshiplinkchain(starting_class, ending_class) -> typing.Optional[tuple]:
    """Find the path to follow to get from the starting table to the ending table."""
    inspected = set()

    def search(_mapper, chain):
        inspected.add(_mapper)
        if _mapper.class_ == ending_class:
            return chain
        relationships = _mapper.relationships
        for _relationship in set(relationships):
            if _relationship.mapper in inspected:
                continue
            result = search(_relationship.mapper, chain + (_relationship,))
            if len(result) != 0:
                return result
        return ()

    return search(inspect(starting_class), tuple())
