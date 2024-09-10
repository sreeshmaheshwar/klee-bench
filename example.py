"""
A short, example benchmarker that compares two KLEE configurations.
"""

from util import ProgressLogger, ResultCSVPrinter
from runklee import run_klee, KleeRunOptions as opts, SearchStrategy
from kresult import KResult, KResultField

import typer
from typing import List


def benchmark(
    time_in_mins: float,
    programs: List[str],
    experiment_name: str = "results",
):
    """
    Run a benchmark comparing unoptimized and optimized DFS KLEE runs.

    Args:
        time_in_mins (float): Time limit for each KLEE run in minutes.
        programs (List[str]): List of programs to benchmark.
        experiment_name (str): Name for the experiment results.
    """
    logger = ProgressLogger()

    printer = ResultCSVPrinter(
        column_names=["Program", "Unoptimised Time (s)", "Optimised Time (s)"],
        experiment_name=experiment_name,
    )

    # Maintain query mismatches for determinism checks, instruction mismatches
    # for error / early termination / bug checking, and instruction list for
    # rerunning and getting set instruction values for future experiments.
    query_mismatches, instr_mismatches, instr_list = [], [], []

    for i, program in enumerate(programs):
        # Baseline KLEE run to get instructions:
        instrs = (
            run_klee(
                opts(
                    name=program,
                    timeToRun=int(time_in_mins * 60),
                    searchStrategy=SearchStrategy.DFS,
                    batchingInstrs=None,
                    memory=2000,
                    dirName="baseline-output",
                    cex=False,
                    independent=False,
                    branch=False,
                ),
                logger=logger,
            ).get(KResultField.INSTRUCTIONS)
            - 200  # Subtract some instructions in case of post-halt overrunning.
        )

        instr_list.append(instrs)

        # Rerun baseline on found instructions.
        unOptResults: KResult = run_klee(
            opts(
                name=program,
                instructions=instrs,
                searchStrategy=SearchStrategy.DFS,
                batchingInstrs=None,
                memory=2000,
                dirName="unoptimised-output",
                cex=False,
                independent=False,
                branch=False,
            ),
            logger=logger,
        )

        # Run testee on found instructions.
        optResults: KResult = run_klee(
            opts(
                name=program,
                instructions=instrs,
                searchStrategy=SearchStrategy.DFS,
                batchingInstrs=None,
                memory=2000,
                dirName="optimised-output",
            ),
            logger=logger,
        )

        if unOptResults.get(KResultField.QUERIES) != optResults.get(
            KResultField.QUERIES
        ):
            query_mismatches.append(
                (
                    program,
                    unOptResults.get(KResultField.QUERIES),
                    optResults.get(KResultField.QUERIES),
                )
            )

        if unOptResults.get(KResultField.INSTRUCTIONS) != optResults.get(
            KResultField.INSTRUCTIONS
        ):
            instr_mismatches.append(
                (
                    program,
                    unOptResults.get(KResultField.INSTRUCTIONS),
                    optResults.get(KResultField.INSTRUCTIONS),
                )
            )

        logger.log_and_print(
            f"""Results for {program} ({i + 1} / {len(programs)}):
    - (First Time: {unOptResults.get(KResultField.TIME)}, Second Time: {optResults.get(KResultField.TIME)})
    - Current query mismatches: {query_mismatches}
    - Current instruction mismatches: {instr_mismatches}"""
        )

        printer.write_row(
            [
                program,
                unOptResults.get(KResultField.TIME),
                optResults.get(KResultField.TIME),
            ]
        )

    logger.log_and_print(f"Printing results...\n{printer.read()}")
    logger.log_and_print(f"Printing instruction list:\n{instr_list}")
    logger.log_and_print(f"Printing query mismatches:\n{query_mismatches}")
    logger.log_and_print(f"Printing instruction mismatches:\n{instr_mismatches}")
    logger.persist_to_file(experiment_name)


if __name__ == "__main__":
    typer.run(benchmark)
