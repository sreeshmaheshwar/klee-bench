"""Run a configured KLEE on Coreutils programs."""

from kresult import KResult
from util import ProgressLogger, klee_exec_path, coreutils_src_path

import datetime
import subprocess

from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional


class Solver(Enum):
    """Supported KLEE SMT solvers."""

    Z3 = "z3"
    STP = "stp"


class SearchStrategy(Enum):
    """Select KLEE search strategies"""

    DefaultHeuristic = "--search=random-path --search=nurs:covnew"
    Inputting = "--search=inputting"
    DFS = "--search=dfs"
    BFS = "--search=bfs"


@dataclass
class KleeRunOptions:
    """
    Configuration options for a KLEE run. Extending this class to add new options
    is easy, but you must also update the `getRunCommand` method of the KleeRunner
    class to handle the new options.
    """

    name: str
    dirName: str  # Also names run statistics csv.
    searchStrategy: SearchStrategy
    batchingInstrs: Optional[int]  # Enables batching search if not None.
    memory: int

    # NOTE: Differs from default - use Z3 for incrementality.
    solver: Solver = Solver.Z3

    # Caches:
    cex: bool = True
    independent: bool = True
    branch: bool = True

    timeToRun: Optional[int] = None  # In seconds.
    instructions: Optional[int] = None

    removeOutput: bool = True

    simplify: bool = True
    solverTimeout: Optional[int] = None

    externalCalls: str = "concrete"  # NOTE: Differs from default.
    dumpStates: bool = False  # NOTE: Differs from default.

    logFile: Optional[str] = None  # Enables SMT2 logging if not None.
    debugDumpZ3File: Optional[str] = None

    additionalOptions: str = ""  # Manual additional options.

    envFile: str = coreutils_src_path("test.env", False)
    runInDir: str = "/tmp/sandbox"

    # Default KLEE Coreutils options:
    simplifySymIndices: bool = True
    writeCvcs: bool = True
    writeCov: bool = True
    outputModule: bool = True
    disableInlining: bool = True
    optimize: bool = True
    useForkedSolver: bool = True
    libc: str = "uclibc"
    posixRuntime: bool = True
    newStates: bool = True
    maxSymArraySize: int = 4096
    maxMemoryInhibit: bool = False
    maxStaticForkPct: int = 1
    maxStaticSolvePct: int = 1
    maxStaticCpforkPct: int = 1
    switchType: str = "internal"

    # Entirely new options:
    stateOutputFile: Optional[str] = None  # State Provision Outputter.
    trOutputFile: Optional[str] = None  # Termination Replaying Outputter.

    stateInputFile: Optional[str] = None  # State Provision Inputter.
    trInputFile: Optional[str] = None  # Termination Replaying Inputter.


SYM_ARGS_EXCEPTIONS = {
    "dd": "--sym-args 0 3 10 --sym-files 1 8 --sym-stdin 8 --sym-stdout",
    "dircolors": "--sym-args 0 3 10 --sym-files 2 12 --sym-stdin 12 --sym-stdout",
    "echo": "--sym-args 0 4 300 --sym-files 2 30 --sym-stdin 30 --sym-stdout",
    "expr": "--sym-args 0 1 10 --sym-args 0 3 2 --sym-stdout",
    "mknod": "--sym-args 0 1 10 --sym-args 0 3 2 --sym-files 1 8 --sym-stdin 8 --sym-stdout",
    "od": "--sym-args 0 3 10 --sym-files 2 12 --sym-stdin 12 --sym-stdout",
    "pathchk": "--sym-args 0 1 2 --sym-args 0 1 300 --sym-files 1 8 --sym-stdin 8 --sym-stdout",
    "printf": "--sym-args 0 3 10 --sym-files 2 12 --sym-stdin 12 --sym-stdout",
}


def sym_args_for_program(name: str) -> str:
    """
    Get the symbolic arguments for a specific Coreutils program.
    See https://klee-se.org/docs/coreutils-experiments/ for more details.

    Args:
        name (str): Name of the Coreutils program.

    Returns:
        str: Symbolic arguments for the program.
    """
    return SYM_ARGS_EXCEPTIONS.get(
        name,
        "--sym-args 0 1 10 --sym-args 0 2 2 --sym-files 1 8 --sym-stdin 8 --sym-stdout",
    )


class KleeRunner:
    """
    A class to configure and run KLEE on Coreutils programs.
    Largely based on KLEE's default Coreutils configuration, found at
    https://klee-se.org/docs/coreutils-experiments/.

    Attributes:
        options (KleeRunOptions): Configuration options for the KLEE run.
        logger (Optional[ProgressLogger]): Logger for progress information.
    """

    def __init__(
        self, options: KleeRunOptions, logger: Optional[ProgressLogger] = None
    ):
        """
        Initialize the KleeRunner.

        Args:
            options (KleeRunOptions): Configuration options for the KLEE run.
            logger (Optional[ProgressLogger]): Logger for progress information.
        """
        self.options = options
        self.logger = logger

    def get_run_command(self) -> List[str]:
        """
        Generate the KLEE run command based on the configuration options.

        Returns:
            str: The complete KLEE run command.
        """

        def arg(k: str, v: Any) -> str:
            return f"--{k}={v}"

        def opt_arg(key: str, optional: Any, value: Any = None) -> str:
            if optional is not None:
                return arg(key, value if value is not None else optional)
            return ""

        o = self.options

        # NOTE: 0 is treated as unset by KLEE for these, we support that too.
        # Prevent indefinite run:
        assert o.timeToRun or o.instructions

        command = [
            klee_exec_path("klee"),
            # Options begin.
            arg("env-file", o.envFile),
            arg("run-in-dir", o.runInDir),
            arg("output-dir", o.dirName),
            arg("solver-backend", o.solver.value),
            opt_arg("max-solver-time", o.solverTimeout),
            arg("simplify-sym-indices", o.simplifySymIndices),
            opt_arg("use-query-log", o.logFile, "all:smt2"),
            arg("write-cvcs", o.writeCvcs),
            arg("write-cov", o.writeCov),
            arg("output-module", o.outputModule),
            arg("max-memory", o.memory),
            arg("disable-inlining", o.disableInlining),
            arg("optimize", o.optimize),
            arg("use-forked-solver", o.useForkedSolver),
            arg("use-cex-cache", o.cex),
            arg("use-independent-solver", o.independent),
            arg("use-branch-cache", o.branch),
            arg("rewrite-equalities", o.simplify),
            arg("libc", o.libc),
            arg("posix-runtime", o.posixRuntime),
            arg("external-calls", o.externalCalls),
            arg("only-output-states-covering-new", o.newStates),
            arg("max-sym-array-size", o.maxSymArraySize),
            arg("max-time", f"{o.timeToRun or 0}s"),
            arg("watchdog", bool(o.timeToRun)),
            arg("max-instructions", o.instructions or 0),
            arg("max-memory-inhibit", o.maxMemoryInhibit),
            arg("max-static-fork-pct", o.maxStaticForkPct),
            arg("max-static-solve-pct", o.maxStaticSolvePct),
            arg("max-static-cpfork-pct", o.maxStaticCpforkPct),
            arg("switch-type", o.switchType),
            arg("dump-states-on-halt", o.dumpStates),
            o.searchStrategy.value,
            opt_arg("use-batching-search", o.batchingInstrs, True),
            opt_arg("batch-instructions", o.batchingInstrs),
            opt_arg("debug-z3-dump-queries", o.debugDumpZ3File),
            opt_arg("state-output", o.stateOutputFile),
            opt_arg("tr-output", o.trOutputFile),
            opt_arg("state-input", o.stateInputFile),
            opt_arg("tr-input", o.trInputFile),
            o.additionalOptions,
            # Options end.
            coreutils_src_path(o.name, True),
            sym_args_for_program(o.name),
        ]

        return list(filter(bool, command))

    def prepare(self) -> None:
        """
        Prepare the environment for the KLEE run by removing existing output directory.
        """
        import os, shutil

        # Remove existing output directory, if it exists.
        if os.path.exists(self.options.dirName) and os.path.isdir(self.options.dirName):
            shutil.rmtree(self.options.dirName)

    def log_command(self, command: List[str]) -> None:
        """
        Log the KLEE run command if a logger is available.

        Args:
            command (List[str]): The KLEE run command to log.
        """
        if self.logger is not None:
            now = datetime.datetime.now()
            self.logger.log_and_print(
                f"At {now}, running command...\n{' '.join(command)}"
            )

    def save_stats(self) -> str:
        """
        Save KLEE statistics to a CSV file.

        Returns:
            str: Path to the saved statistics CSV file.
        """
        klee_stats_path = f"{self.options.dirName}.stats.csv"

        command = [
            klee_exec_path("klee-stats"),
            "--table-format=csv",
            "--print-all",
            self.options.dirName,
        ]

        with open(klee_stats_path, "w") as f:
            subprocess.run(command, stdout=f)

        return klee_stats_path

    def cleanup(self) -> None:
        """
        Perform cleanup operations after the KLEE run, by renaming log files
        and removing the output directory if specified.
        """
        if self.options.logFile is not None:
            logPath = f"{self.options.dirName}/all-queries.smt2"
            subprocess.run(["mv", logPath, self.options.logFile])

        if self.options.removeOutput:
            subprocess.run(["rm", "-rf", self.options.dirName])

    def run(self) -> KResult:
        """
        Execute the KLEE run with the configured options.

        Returns:
            KResult: The results of the KLEE run.
        """
        self.prepare()

        command = self.get_run_command()
        self.log_command(command)

        subprocess.run(
            command
        )  # Must not set `check=True`. TODO: Catch the error instead?

        klee_stats_path = self.save_stats()
        results = KResult.from_csv(klee_stats_path)

        self.cleanup()

        return results


def run_klee(
    options: KleeRunOptions, logger: Optional[ProgressLogger] = None
) -> KResult:
    """
    Convenience function to run KLEE with the given options.

    Args:
        options (KleeRunOptions): Configuration options for the KLEE run.
        logger (Optional[ProgressLogger]): Logger for progress information.

    Returns:
        KResult: The results of the KLEE run.
    """
    return KleeRunner(options, logger).run()
