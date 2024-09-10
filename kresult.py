"""Classes and methods to handle and represent results of a KLEE run."""

import json

from enum import Enum
from typing import Any, Dict


class KResultField(Enum):
    """Enumeration of KLEE result fields."""

    TIME = "Time(s)"
    INSTRUCTIONS = "Instrs"
    ICOV_PERCENT = "ICov(%)"
    BCOV_PERCENT = "BCov(%)"
    ICOUNT = "ICount"
    TSOLVER_PERCENT = "TSolver(%)"
    ICOVERED = "ICovered"
    IUNCOVERED = "IUncovered"
    BRANCHES = "Branches"
    FULL_BRANCHES = "FullBranches"
    PARTIAL_BRANCHES = "PartialBranches"
    EXTERNAL_CALLS = "ExternalCalls"
    TUSER_SECONDS = "TUser(s)"
    TRESOLVE_SECONDS = "TResolve(s)"
    TRESOLVE_PERCENT = "TResolve(%)"
    TCEX_SECONDS = "TCex(s)"
    TCEX_PERCENT = "TCex(%)"
    TQUERY_SECONDS = "TQuery(s)"
    TSOLVER_SECONDS = "TSolver(s)"
    STATES = "States"
    ACTIVE_STATES = "ActiveStates"
    MAX_ACTIVE_STATES = "MaxActiveStates"
    AVG_ACTIVE_STATES = "AvgActiveStates"
    INHIBITED_FORKS = "InhibitedForks"
    QUERIES = "Queries"
    SOLVER_QUERIES = "SolverQueries"
    SOLVER_QUERY_CONSTRUCTS = "SolverQueryConstructs"
    QCACHE_MISSES = "QCacheMisses"
    QCACHE_HITS = "QCacheHits"
    QCEX_CACHE_MISSES = "QCexCacheMisses"
    QCEX_CACHE_HITS = "QCexCacheHits"
    ALLOCATIONS = "Allocations"
    MEM_MIB = "Mem(MiB)"
    MAX_MEM_MIB = "MaxMem(MiB)"
    AVG_MEM_MIB = "AvgMem(MiB)"
    BR_CONDITIONAL = "BrConditional"
    BR_INDIRECT = "BrIndirect"
    BR_SWITCH = "BrSwitch"
    BR_CALL = "BrCall"
    BR_MEM_OP = "BrMemOp"
    BR_RESOLVE_POINTER = "BrResolvePointer"
    BR_ALLOC = "BrAlloc"
    BR_REALLOC = "BrRealloc"
    BR_FREE = "BrFree"
    BR_GET_VAL = "BrGetVal"
    TERM_EXIT = "TermExit"
    TERM_EARLY = "TermEarly"
    TERM_SOLVER_ERR = "TermSolverErr"
    TERM_PROGR_ERR = "TermProgrErr"
    TERM_USER_ERR = "TermUserErr"
    TERM_EXEC_ERR = "TermExecErr"
    TERM_EARLY_ALGO = "TermEarlyAlgo"
    TERM_EARLY_USER = "TermEarlyUser"
    TARRAY_HASH_SECONDS = "TArrayHash(s)"
    TFORK_SECONDS = "TFork(s)"
    TFORK_PERCENT = "TFork(%)"
    TUSER_PERCENT = "TUser(%)"


class KResult(object):
    """A class to represent KLEE execution results."""

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a KResult instance.

        Args:
            data (Dict[str, Any]): A dictionary containing KLEE result data
            as output by `klee-stats`.
        """
        self._data = data

    def get(self, field: KResultField) -> Any:
        """
        Retrieve a value from the KLEE result data.

        Args:
            field (KResultField): The field to retrieve.

        Returns:
            Any: The value associated with the given field, parsed appropriately.
        """
        return self._parse_value(self._data.get(field.value))

    def to_json(self) -> str:
        """
        Convert the KLEE result data to a JSON string.

        Returns:
            str: A JSON representation of the KLEE result data.
        """
        return json.dumps(self._data, indent=2)

    @classmethod
    def from_csv(cls, csv_path: str) -> "KResult":
        """
        Create a KResult instance from a CSV file.

        Args:
            csv_path (str): The path to the CSV file containing KLEE result data.

        Returns:
            KResult: A new KResult instance created from the CSV data.

        Raises:
            AssertionError: If the CSV file contains more than one row of data.
        """
        from util import dict_from_csv

        data = dict_from_csv(csv_path)
        assert len(data) == 1, "Expected exactly one row of data"
        return cls(data[0])

    @staticmethod
    def _parse_value(value: str) -> Any:
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        print(KResult.from_csv(sys.argv[1]).to_json())
    else:
        print("Usage: python kresult.py <csv_file_path>")
        sys.exit(1)
