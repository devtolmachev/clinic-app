"""Contains functions and classes for work with cdv."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd
from clinic_app.shared import CSVS


class CSVFile:
    """Interface to interact with csv files.

    Parameters
    ----------
    path : str
        Path to csv file.

    """

    def __init__(self, path: str) -> None:
        if not Path(path).exists():
            raise FileNotFoundError(path)
        if not path.endswith(".csv"):
            raise ValueError

        self.path = path

    def create_column(self, column_name: str) -> None:
        """Create column with empty rows in csv file."""
        df = self.get_df()
        df[column_name] = [None] * len(df)
        df.to_csv(self.path, index=False)

    def get_df(self) -> pd.DataFrame:
        """Get `pd.DataFrame` from csv.

        Returns
        -------
        pd.DataFrame
            dataframe.
        """
        return pd.read_csv(self.path)

    def value_exists(self, value: Any, column_name: str) -> bool:
        """Return True if value exists, otherwise False.

        Parameters
        ----------
        value : Any
            The value to need find.
        column_name : str
            Column name in which value are located.

        Returns
        -------
        bool
            True if value exists, otherwise False.
        """
        df = self.get_df()
        exists = df[column_name].isin([value]).any()
        return bool(exists)

    def find_and_replace(
        self,
        search_value_column_name: str,
        search_value: str,
        new_value_column_name: str,
        new_value: str,
        save: bool = False,
    ) -> pd.DataFrame:
        """Find value by column name and replace it.

        Parameters
        ----------
        search_value_column_name : str
            column name in which value source are located.
        search_value : str
            source value.
        new_value_column_name : str
            Name of the column in which the cell should be updated.
        new_value : str
            New value.
        save : bool, optional
            If True it DataFrame will saved to .csv, by default False.

        Returns
        -------
        pd.DataFrame
            Updated DataFrame.
        """
        df = self.get_df()
        # Get a row index
        index = df.loc[df[search_value_column_name] == search_value].index[0]
        df.at[index, new_value_column_name] = new_value
        if save:
            df.to_csv(self.path, index=False)
        return df


class Database(CSVFile):
    def __init__(self, path: Optional[str] = None) -> None:
        if not path:
            path = CSVS["db"]
        if not Path(path).exists():
            with open(path, "w"):
                pass

        super().__init__(path=path)

    def get_value_by_kv(self, kv: tuple[str, Any], column: str) -> Any | None:
        df = self.get_df()
        filtered = df.loc[df[kv[0]] == kv[1], column]

        if filtered.empty:
            return None

        return filtered.iloc[0]
