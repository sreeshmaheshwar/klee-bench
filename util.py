"""Utility functions and classes for KLEE and Coreutils experiments."""

import csv
import os
from typing import List, Dict

# Environment variables for paths
KLEE_BIN_PATH = os.getenv("KLEE_BIN_ABS_PATH")
COREUTILS_SRC_PATH = os.getenv("COREUTILS_SRC_ABS_PATH")

# Directory constants
RESULTS_DIR = "results"
PROGRESS_DIR = "progress"


def klee_exec_path(exec_name: str) -> str:
    """
    Get the full path to a KLEE executable.

    Args:
        exec_name (str): The name of the executable.

    Returns:
        str: The full path to the KLEE executable.
    """
    return os.path.join(KLEE_BIN_PATH, exec_name)


def coreutils_src_path(name: str, program: bool = True) -> str:
    """
    Get the full path to a Coreutils file.

    Args:
        name (str): The name of the file.
        program (bool): Whether the file is a Coreutils program.

    Returns:
        str: The full path to the Coreutils file.
    """
    if program and not name.endswith(".bc"):
        name += ".bc"

    return os.path.join(COREUTILS_SRC_PATH, name)


def dict_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """
    Read a CSV file and return its contents as a list of dictionaries.

    Args:
        csv_path (str): The path to the CSV file.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, where each dictionary
        represents a row in the CSV file.
    """
    with open(csv_path, "r") as file:
        csv_reader = csv.DictReader(file)
        return list(csv_reader)


class ProgressLogger:
    """A class for logging progress during long-running experiments."""

    def __init__(self, progress_file: str = "progress.txt"):
        """
        Initialize the ProgressLogger.

        Args:
            progress_file (str): The name of the file to log progress to.
        """
        self.progress_file = progress_file
        with open(self.progress_file, "w") as f:
            f.write("")

    def log(self, progress: str) -> None:
        """
        Log a progress message to the file.

        Args:
            progress (str): The progress message to log.
        """
        with open(self.progress_file, "a") as f:
            f.write(f"{progress}\n\n\n")

    def log_and_print(self, progress: str) -> None:
        """
        Log a progress message and print it to the console.

        Args:
            progress (str): The progress message to log and print.
        """
        print(f"\n\n{progress}\n\n")
        self.log(progress)

    def persist_to_file(
        self, file: str, append_txt: bool = True, prepend_progress: bool = True
    ) -> None:
        """
        Save the progress log to a separate file.

        Args:
            file (str): The name of the file to save the progress log to.
            append_txt (bool): Whether to append '.txt' to the filename.
            prepend_progress (bool): Whether to prepend the progress directory path.
        """
        if append_txt:
            file = f"{file}.txt"

        if prepend_progress:
            os.makedirs(PROGRESS_DIR, exist_ok=True)
            file = os.path.join(PROGRESS_DIR, file)

        with open(file, "w") as dest, open(self.progress_file, "r") as src:
            dest.write(src.read())


class ResultCSVPrinter:
    """A class for writing and reading experiment results in CSV format."""

    def __init__(
        self,
        column_names: List[str],
        experiment_name: str,
        append_csv: bool = True,
        prepend_results: bool = True,
    ):
        """
        Initialize the ResultCSVPrinter.

        Args:
            column_names (List[str]): The names of the columns in the CSV file.
            experiment_name (str): The name of the experiment (used for the filename).
            append_csv (bool): Whether to append '.csv' to the filename.
            prepend_results (bool): Whether to prepend the results directory path.
        """
        self.columns = column_names

        if append_csv:
            experiment_name = f"{experiment_name}.csv"

        if prepend_results:
            os.makedirs(RESULTS_DIR, exist_ok=True)
            self.csv_file = os.path.join(RESULTS_DIR, experiment_name)
        else:
            self.csv_file = experiment_name

        with open(self.csv_file, "w") as f:
            f.write(",".join(column_names) + "\n")

    def write_row(self, row: List[str]) -> None:
        """
        Write a row of data to the CSV file.

        Args:
            row (List[str]): The data to write as a row in the CSV file.

        Raises:
            AssertionError: If the number of items in the row doesn't match the number of columns.
        """
        assert len(row) == len(
            self.columns
        ), "Row length must match the number of columns"
        with open(self.csv_file, "a") as f:
            f.write(",".join(map(str, row)) + "\n")

    def read(self) -> str:
        """
        Read the contents of the CSV file.

        Returns:
            str: The contents of the CSV file as a string.
        """
        with open(self.csv_file, "r") as f:
            return f.read()
