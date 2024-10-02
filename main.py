from util import *
from runklee import run_klee, KleeRunOptions as opts, SearchStrategy
from kresult import KResultField

import os

VM_ID = int(os.getenv("VM_ID"))
REPLAY_LOCATION = os.getenv(
    "REPLAY_LOCATION"
)  # Absolute path of where to store compressed states and termination replays.

# TODO: Normal is 10000.
BATCHING_INSTRS = 1000

INSTRUCTION_OFFSET = 200

# TODO: Increase when time increases
BASELINE_RUN_TIME = 2

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


def runBaselines():
    assert 0 <= VM_ID < len(PROGRAMS)
    p = PROGRAMS[VM_ID]
    logger = ProgressLogger()

    stateReplayFile = f"{REPLAY_LOCATION}/{p}-states.gz"
    trReplayFile = f"{REPLAY_LOCATION}/{p}-tr.gz"

    buildBranch("deterministic-mainline")
    instructions = (
        run_klee(
            opts(
                name=p,
                searchStrategy=SearchStrategy.DefaultHeuristic,
                batchingInstrs=1000,  # NB: Normal is 10000.
                memory=1500,
                dirName=f"mainline-supplier-{p}",
                timeToRun=int(BASELINE_RUN_TIME * 60),
                stateOutputFile=stateReplayFile[:-3],  # Remove .gz
                trOutputFile=trReplayFile[:-3],  # Remove .gz
            ),
            logger=logger,
        ).get(KResultField.INSTRUCTIONS)
        - INSTRUCTION_OFFSET
    )

    # Replay baseline together with strategies to test.
    for branch, options, approachName in [
        ("", "", "mainline"),
        ("s2g-base", "", "s2g"),
        ("s2g-base", "--inc-timeout=1000", "s2g-timeout"),
    ]:
        if branch:
            buildBranch(branch)

        current = run_klee(
            opts(
                name=p,
                searchStrategy=SearchStrategy.Inputting,
                batchingInstrs=BATCHING_INSTRS,  # NB: Normal is 10000.
                memory=1500,  # Does not matter (yet).
                dirName=f"{approachName}-{p}",
                timeToRun=int(MAX_TIMEOUT_MINS * 60),
                instructions=instructions,
                stateInputFile=stateReplayFile,
                trInputFile=trReplayFile,
                additionalOptions=options,
            ),
            logger=logger,
        ).get(KResultField.INSTRUCTIONS)

        if current != instructions:
            logger.log_and_print(f"!!! Mismatch for {p}: {instructions} vs {current}")


if __name__ == "__main__":
    runBaselines()
