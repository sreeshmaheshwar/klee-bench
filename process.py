from kresult import *
from plot import *
from util import *

from dataclasses import dataclass

ALL_COREUTIL_PROGRAMS = [
    "base64",
]

@dataclass
class StrategyToProcess:
    prettyName: str

    # Name from program, that should take a program name and return the stats file name
    nameFromProgram: any

STRATEGIES = [
    StrategyToProcess("Mainline", lambda p: f"mainline-{p}"),
    StrategyToProcess("Solver2Basic", lambda p: f"s2g-{p}"),
    # StrategyToProcess("Solver2Timeout", lambda p: f"s2g-timeout-{p}"),
    StrategyToProcess("LCP-Pooling", lambda p: f"lcp-pooling-{p}"),
    StrategyToProcess("CSA-TR", lambda p: f"csa-tr-{p}"),
    StrategyToProcess("LCP-PP", lambda p: f"lcp-pp-improved-arrays-{p}"),
    StrategyToProcess("Partition-Early", lambda p: f"pe-{p}")
]

def extractColumn(
    programs,
    ylabel,
    output,
    strategies=STRATEGIES,
    fieldName=None,
    dictFun=None,
    colours=DEFAULT_COLOURS,
):
    prettyNames = [s.prettyName for s in strategies]
    rcp = ResultCSVPrinter(["Program"] + prettyNames, output)

    for program in programs:
        row = [program]

        for strategy in strategies:
            results = KResult.from_csv(f"{strategy.nameFromProgram(program)}.stats.csv")
            if fieldName:
                row.append(results.get(fieldName))
            else:
                assert dictFun is not None
                row.append(dictFun(results._data))

        rcp.write_row(row)

    path = generateTex(rcp.csv_file, False, ylabel=ylabel, colours=colours)

    os.system("mkdir charts")
    os.system(f"pdflatex --output-directory=charts {path}")
    # Remove the aux files and the log files.
    os.system(f"rm -rf charts/*.aux")
    os.system(f"rm -rf charts/*.log")


if __name__ == "__main__":
    extractColumn(
        programs=ALL_COREUTIL_PROGRAMS,
        fieldName=KResultField.QUERIES,
        output="Queries",
        ylabel="Queries",
    )

    extractColumn(
        programs=ALL_COREUTIL_PROGRAMS,
        fieldName=KResultField.MAX_MEM_MIB,
        output="MaxMem",
        ylabel="Max Memory (MiB)",
    )

    extractColumn(
        programs=ALL_COREUTIL_PROGRAMS,
        fieldName=KResultField.TSOLVER_SECONDS,
        output="TSolver",
        ylabel="Solver Time (s)",
    )

    extractColumn(
        programs=ALL_COREUTIL_PROGRAMS,
        fieldName=KResultField.TQUERY_SECONDS,
        output="TQuery",
        ylabel="Core Solver Time (s)",
    )

    extractColumn(
        programs=ALL_COREUTIL_PROGRAMS,
        fieldName=KResultField.TIME,
        output="Times",
        ylabel="Time (s)",
    )

    extractColumn(
        programs=ALL_COREUTIL_PROGRAMS,
        dictFun=lambda d: float(d["TSolver(s)"]) - float(d["TCex(s)"]),
        output="SolverMinusCex",
        ylabel="Solver Time - Cex Time (s)",
    )

    extractColumn(
        programs=ALL_COREUTIL_PROGRAMS,
        dictFun=lambda d: float(d["TSolver(s)"]) - float(d["TQuery(s)"]),
        output="SolverMinusCore",
        ylabel="Solver Chain Time - Core Solver Time (s)",
    )
