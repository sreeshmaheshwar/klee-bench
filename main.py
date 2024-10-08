from util import *
from runklee import run_klee, KleeRunOptions as opts, SearchStrategy
from kresult import KResult, KResultField
from collections import namedtuple

import os

VM_ID = int(os.getenv("VM_ID"))
REPLAY_LOCATION = os.getenv(
    "REPLAY_LOCATION"
)  # Absolute path of where to store compressed states and termination replays.

# TODO: Normal is 10000.
BATCHING_INSTRS = 1000

INSTRUCTION_OFFSET = 200

# TODO: Increase when time increases
BASELINE_RUN_TIME = 5

# TODO: Increase when time increases
MAX_TIMEOUT_MINS = 30

# Eight programs tested in Individual Project evaluation.
PROGRAMS = [
    "base64",
    "dircolors",
    "fold",
    "ln",
    "mkfifo",
    "nice",
    "od",
    "unexpand",
]


def buildBranch(branchName):
    curDir = os.getcwd()
    os.chdir(f"{KLEE_BIN_PATH}/..")
    os.system("git fetch --all")
    os.system(f"git checkout {branchName}")
    os.system("git pull")
    os.system("make")
    os.chdir(curDir)


def runBaseline(logger):
    assert 0 <= VM_ID < len(PROGRAMS)
    p = PROGRAMS[VM_ID]

    buildBranch("deterministic-mainline")
    run_klee(
        opts(
            name=p,
            searchStrategy=SearchStrategy.DefaultHeuristic,
            batchingInstrs=1000,  # NB: Normal is 10000.
            memory=2000,
            dirName=f"mainline-supplier-{p}",
            timeToRun=int(BASELINE_RUN_TIME * 60),
        ),
        logger=logger,
    )


ApproachToTest = namedtuple("ApproachToTest", ["branch", "approachName", "options"])


def runTargets(
    logger: ProgressLogger,
    approaches: List[ApproachToTest],
):
    assert 0 <= VM_ID < len(PROGRAMS)
    p = PROGRAMS[VM_ID]

    instructions = (
        KResult.from_csv(f"mainline-supplier-{p}.stats.csv").get(
            KResultField.INSTRUCTIONS
        )
        - INSTRUCTION_OFFSET
    )

    for branch, approachName, options in approaches:
        if branch:
            buildBranch(branch)

        o = opts(
            name=p,
            # cex=False,
            # independent=False,
            # branch=False,
            searchStrategy=SearchStrategy.DFS,
            memory=2000,  # Now it matters.
            dirName=f"{approachName}-{p}",
            timeToRun=int(MAX_TIMEOUT_MINS * 60),
            instructions=instructions,
            additionalOptions=options,
        )

        current = run_klee(
            options=o,
            logger=logger,
        ).get(KResultField.INSTRUCTIONS)

        if current != instructions:
            logger.log_and_print(f"!!! Mismatch for {p}: {instructions} vs {current}")


if __name__ == "__main__":
    logger = ProgressLogger()

    # Baseline run:
    runBaseline(logger)

    # Rerun baseline with approaches:
    # runTargets(
    #     logger,
    #     [
    #         ApproachToTest("deterministic-mainline", "mainline", ""),
    #         ApproachToTest("s2g-base", "s2g", ""),
    #         ApproachToTest("s2g-base", "s2g-timeout", "--inc-timeout=1000"),
    #     ],
    # )

    # TODO: Add incremental timeout.
    runTargets(
        logger,
        [
            # ApproachToTest("lcp-pp-original", "lcp-pp-original", ""),
            # ApproachToTest("lcp-pp-improved-arrays", "lcp-pp-improved-arrays", ""),
            # ApproachToTest("lcp-pooling", "lcp-pooling", ""),
            ApproachToTest("csa-tr-attempt", "csa-tr", "--restart-interval=500")
            # ApproachToTest("partition-early-improved", "pe", "")
        ]
    )
