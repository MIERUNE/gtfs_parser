import glob
import os
import zipfile
import pandas as pd
import io


def append_table(f: io.BufferedIOBase, table_path: str, table_dfs: dict):
    datatype = os.path.splitext(os.path.basename(table_path))[0]
    df = pd.read_csv(f, dtype=str)
    table_dfs[datatype] = df


def GTFS(gtfs_path: str) -> dict:
    """
    read GTFS file to memory.

    Args:
        path of zip file or directory containing txt files.
    Returns:
        dict: tables
    """
    tables = {}
    path = os.path.join(gtfs_path)
    if os.path.isdir(path):
        table_files = glob.glob(os.path.join(gtfs_path, "*.txt"))
        for table_file in table_files:
            with open(table_file, encoding="utf-8_sig") as f:
                append_table(f, table_file, tables)
    else:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"zip file not found. ({path})")
        with zipfile.ZipFile(path) as z:
            for file_name in z.namelist():
                if file_name.endswith(".txt") and os.path.basename(file_name) == file_name:
                    with z.open(file_name) as f:
                        append_table(f, file_name, tables)

    # check files.
    if len(tables) == 0:
        raise FileNotFoundError("txt files must reside at the root level directly, not in a sub folder.")

    required_tables = {"agency", "stops", "routes", "trips", "stop_times"}
    missing_tables = [req for req in required_tables if req not in tables]
    if len(missing_tables) > 0:
        raise FileNotFoundError(f"there are missing required files({','.join(missing_tables)}).")

    # cast some columns
    cast_columns = {
        "stops": {"stop_lon": float, "stop_lat": float},
        "stop_times": {"stop_sequence": int},
        "shapes": {"shape_pt_lon": float, "shape_pt_lat": float, "shape_pt_sequence": int},
    }
    for table, casts in cast_columns.items():
        if table in tables:
            tables[table] = tables[table].astype(casts)

    # Set null values on optional columns used in this module.
    if "parent_station" not in tables["stops"].columns:
        tables["stops"]["parent_station"] = None

    # set agency_id when there is a single agency
    agency_df = tables["agency"]
    if len(agency_df) == 1:
        if "agency_id" not in agency_df.columns or pd.isnull(agency_df["agency_id"].iloc[0]):
            agency_df["agency_id"] = ""
        agency_id = agency_df['agency_id'].iloc[0]
        tables["routes"]["agency_id"] = agency_id

    return tables
