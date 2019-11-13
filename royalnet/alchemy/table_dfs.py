try:
    from sqlalchemy.inspection import inspect
    from sqlalchemy.schema import Table
except ImportError:
    inspect = None
    Table = None


def table_dfs(starting_table: Table, ending_table: Table) -> tuple:
    """Depth-first-search for the path from the starting table to the ending table.

    Returns:
        A :class:`tuple` containing the path, starting from the starting table and ending at the ending table."""
    if inspect is None:
        raise ImportError("'alchemy' extra is not installed")

    inspected = set()

    def search(_mapper, chain):
        inspected.add(_mapper)
        if _mapper.class_ == ending_table:
            return chain
        relationships = _mapper.relationships
        for _relationship in set(relationships):
            if _relationship.mapper in inspected:
                continue
            result = search(_relationship.mapper, chain + (_relationship,))
            if len(result) != 0:
                return result
        return ()

    return search(inspect(starting_table), tuple())
