import csv
import os.path as path
from datetime import datetime
from glob import iglob
from os import makedirs
from typing import Tuple, Union
import numpy as np
import yaml
from scipy.interpolate import interp1d


def _set_params(conf_file: Union[str, None] = None) -> None:
    global ROOT_DIR, INERTIAL_SENSOR_LIST, ENABLE_BLE, FREQ

    ROOT_DIR = path.join(path.dirname(__file__), "../")

    if conf_file is None:
        conf_file = path.join(ROOT_DIR, "config/default.yaml")    # load default config file

    with open(conf_file) as f:
        conf: dict = yaml.safe_load(f)
    INERTIAL_SENSOR_LIST = np.array(conf["inertial_sensor"], dtype=str)
    ENABLE_BLE = bool(conf["enable_ble"])
    FREQ = np.float16(conf["freq"])

def _load_log(src_file: str) -> Tuple[np.ndarray, np.ndarray]:
    inertial = np.empty(len(INERTIAL_SENSOR_LIST), dtype=np.ndarray)
    for i in range(len(INERTIAL_SENSOR_LIST)):
        inertial[i] = np.empty((0, 4), dtype=np.float64)    # (timestamp, x, y, z)
    ble = np.empty(3, dtype=np.ndarray)
    ble[0] = np.empty(0, dtype=np.float64)    # timestamp
    ble[1] = np.empty(0, dtype=str)           # MAC address
    ble[2] = np.empty(0, dtype=np.int8)       # RSSI (>= -128)

    with open(src_file) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            for i, s in enumerate(INERTIAL_SENSOR_LIST):
                if row[1] == s:
                    row_2 = row[2].split(",")[1:]
                    inertial[i] = np.vstack((inertial[i], (np.float64(row[0]), np.float64(row_2[0]), np.float64(row_2[1]), np.float64(row_2[2]))))

            if ENABLE_BLE and row[1] == "BLE":
                row_2 = row[2].split(",")
                ble[0] = np.hstack((ble[0], np.float64(row[0])))
                ble[1] = np.hstack((ble[1], row_2[0].lower()))
                ble[2] = np.hstack((ble[2], np.int8(row_2[1])))

    print(f"{path.basename(src_file)} has been loaded")

    return inertial, ble

def _resample_inertial_log(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    start: np.float64 = max([d[0, 0] for d in data])
    stop: np.float64 = min([d[-1, 0] for d in data])
    resampled_ts: np.ndarray = np.arange(start, stop, step=1/FREQ, dtype=np.float64)

    resampled_val = np.empty((len(resampled_ts), 3 * len(INERTIAL_SENSOR_LIST)), np.float64)
    for i, d in enumerate(data):
        for j in range(3):
            resampled_val[:, 3*i+j] = interp1d(d[:, 0], d[:, j+1])(resampled_ts)

    return resampled_ts, resampled_val

def _convert_from_unix_to_datetime(ts: np.ndarray) -> np.ndarray:
    ts = ts.astype(object)    # enable to store datetime

    for i, t in enumerate(ts):
        ts[i] = datetime.fromtimestamp(t)

    return ts.astype(datetime)

def _format_log(src_file: str, tgt_dir: str) -> None:
    inertial, ble = _load_log(src_file)
    
    resampled_ts, resampled_val = _resample_inertial_log(inertial)
    resampled_ts = _convert_from_unix_to_datetime(resampled_ts)

    if not path.exists(path.join(tgt_dir, "inertial/")):
        makedirs(path.join(tgt_dir, "inertial/"))
    tgt_file = path.join(tgt_dir, "inertial/", str(resampled_ts[0].date()) + "_" + path.basename(src_file)[:-4] + ".csv")
    with open(tgt_file, "w") as f:
        writer = csv.writer(f)
        for i, t in enumerate(resampled_ts):
            writer.writerow((t.strftime("%Y-%m-%d %H:%M:%S.%f"), *resampled_val[i]))

    print(f"written to inertial/{path.basename(tgt_file)}")

    if ENABLE_BLE:
        ble[0] = _convert_from_unix_to_datetime(ble[0])

        if not path.exists(path.join(tgt_dir, "ble/")):
            makedirs(path.join(tgt_dir, "ble/"))
        tgt_file = path.join(tgt_dir, "ble/", str(ble[0][0].date()) + ".csv")
        with open(tgt_file, "w") as f:
            writer = csv.writer(f)
            for i, t in enumerate(ble[0]):
                writer.writerow((t.strftime("%Y-%m-%d %H:%M:%S.%f"), ble[1][i], ble[2][i]))

        print(f"written to ble/{path.basename(tgt_file)}")

def format_logs(src_file: Union[str, None] = None, src_dir: Union[str, None] = None, tgt_dir: Union[str, None] = None) -> None:
    if tgt_dir is None:
        tgt_dir = path.join(ROOT_DIR, "formatted/")    # save to default target directory

    if src_file is None and src_dir is None:
        for src_file in iglob(path.join(ROOT_DIR, "raw/*.log")):    # loop for default source directory
            _format_log(src_file, tgt_dir)

    elif src_file is None:
        for src_file in iglob(src_dir):    # loop for specified source directory
            _format_log(src_file, tgt_dir)

    elif src_dir is None:
        _format_log(src_file, tgt_dir)

    else:
        raise Exception("'src_file' and 'src_dir' are specified at the same time")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="specify config file", metavar="PATH_TO_CONFIG_FILE")
    parser.add_argument("--src_file", help="specify source file", metavar="PATH_TO_SRC_FILE")
    parser.add_argument("--src_dir", help="specify source directory", metavar="PATH_TO_SRC_DIR")
    parser.add_argument("--tgt_dir", help="specify target directory", metavar="PATH_TO_TGT_DIR")
    args = parser.parse_args()
    
    _set_params(args.config)

    format_logs(args.src_file, args.src_dir, args.tgt_dir)
