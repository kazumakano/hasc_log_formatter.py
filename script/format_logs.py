import argparse
import csv
import os.path as path
from datetime import datetime
from glob import iglob
from typing import Tuple, Union
import numpy as np
from scipy.interpolate import interp1d

FREQ = 100
ROOT_DIR = path.dirname(__file__) + "/../"
SENSOR_LIST = ("ACC", "GYRO")

def _load(src_file: str) -> np.ndarray:
    data = np.empty(len(SENSOR_LIST), dtype=np.ndarray)
    for i in range(len(SENSOR_LIST)):
        data[i] = np.empty((0, 4), dtype=np.float64)

    with open(src_file) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            for i, s in enumerate(SENSOR_LIST):
                if row[1] == s:
                    row_2 = row[2].split(",")[1:]
                    data[i] = np.vstack((data[i], (np.float64(row[0]), np.float64(row_2[0]), np.float64(row_2[1]), np.float64(row_2[2]))))
    
    print(f"{path.basename(src_file)} has been loaded")

    return data

def _resample(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    start = max([d[0, 0] for d in data])
    stop = min([d[-1, 0] for d in data])
    resampled_ts: np.ndarray = np.arange(start, stop, step=1/FREQ, dtype=np.float64)

    resampled_val = np.empty((len(resampled_ts), 3 * len(SENSOR_LIST)), np.float64)
    for i, d in enumerate(data):
        for j in range(3):
            resampled_val[:, 3 * i + j] = interp1d(d[:, 0], d[:, j+1])(resampled_ts)

    return resampled_ts, resampled_val

def _convert_from_unix_to_datetime(ts: np.ndarray) -> np.ndarray:
    ts = ts.astype(object)    # enable to store datetime

    for i, t in enumerate(ts):
        ts[i] = datetime.fromtimestamp(t)
    
    return ts

def _format_log(src_file: str, tgt_dir: str) -> None:
    resampled_ts, resampled_val = _resample(_load(src_file))
    resampled_ts = _convert_from_unix_to_datetime(resampled_ts)

    tgt_file = tgt_dir + str(resampled_ts[0].date()) + "_" + path.basename(src_file)[:-4] + ".csv"
    with open(tgt_file, "w") as f:
        writer = csv.writer(f)
        writer.writerows(np.hstack((resampled_ts[:, np.newaxis], resampled_val)))
    
    print(f"written to {path.basename(tgt_file)}")

def format_logs(src_file: Union[str, None] = None, src_dir: Union[str, None] = None, tgt_dir: Union[str, None] = None) -> None:
    if tgt_dir is None:
        tgt_dir = ROOT_DIR + "formatted/"    # save to default target directory

    if src_file is None and src_dir is None:
        for src_file in iglob(ROOT_DIR + "raw/*.log"):    # loop for default source directory
            _format_log(src_file, tgt_dir)

    elif src_file is None:
        for src_file in iglob(src_dir):    # loop for specified source directory
            _format_log(src_file, tgt_dir)

    elif src_dir is None:
        _format_log(src_file, tgt_dir)

    else:
        raise Exception("'src_file' and 'src_dir' are specified at the same time")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src_file", help="specify source file", metavar="PATH_TO_SRC_FILE")
    parser.add_argument("--src_dir", help="specify source directory", metavar="PATH_TO_SRC_DIR")
    parser.add_argument("--tgt_dir", help="specify target directory", metavar="PATH_TO_TGT_DIR")
    args = parser.parse_args()
    
    format_logs(args.src_file, args.src_dir, args.tgt_dir)
