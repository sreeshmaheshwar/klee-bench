from runklee import run_klee, KleeRunOptions as opts, SearchStrategy
from kresult import KResult, KResultField
from util import ProgressLogger

if __name__ == '__main__':
    logger = ProgressLogger()
    i = run_klee(
        opts(
            name="base64",
            searchStrategy=SearchStrategy.DFS,
            timeToRun=10,
            batchingInstrs=None,
            memory=2000,
            dirName="buffer-output",
            # stateOutputFile="/home/sreesh/base64-states",
            # trOutputFile="/home/sreesh/base64-tr",
        ),
        logger=logger
    ).get(KResultField.INSTRUCTIONS)

    # run_klee(
    #     opts(
    #         name="base64",
    #         searchStrategy=SearchStrategy.Inputting,
    #         batchingInstrs=None,
    #         instructions=i,
    #         memory=2000,
    #         dirName="buffer-output",
    #         stateInputFile="/home/sreesh/base64-states.gz",
    #         trInputFile="/home/sreesh/base64-tr.gz",
    #     ),
    #     logger=logger
    # )