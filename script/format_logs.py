from __future__ import annotations
import csv
import os.path as path
import pickle
from datetime import datetime
from glob import iglob
from os import mkdir
from typing import Any, Optional
import numpy as np
import yaml
from scipy.interpolate import interp1d


def _set_params(conf_file: str | None) -> None:
    global ROOT_DIR, INERTIAL_SENSORS, ENABLE_BLE, FREQ

    ROOT_DIR = path.join(path.dirname(__file__), "../")

    if conf_file is None:
        conf_file = path.join(ROOT_DIR, "config/default.yaml")
    print(f"{path.basename(conf_file)} has been loaded")

    with open(conf_file) as f:
        conf: dict[str, Any] = yaml.safe_load(f)
    ENABLE_BLE = bool(conf["enable_ble"])
    FREQ = np.float32(conf["freq"])
    INERTIAL_SENSORS = tuple(conf["inertial_sensors"])

def _load_log(file: str) -> tuple[np.ndarray, np.ndarray]:
    inertial = np.empty(len(INERTIAL_SENSORS), dtype=np.ndarray)
    for i, s in enumerate(INERTIAL_SENSORS):
        if s in ("ACC", "GRAV", "GYRO", "MAG"):
            inertial[i] = np.empty((0, 4), dtype=np.float64)    # (timestamp, x, y, z)
        elif s == "ROTV":
            inertial[i] = np.empty((0, 5), dtype=np.float64)    # (timestamp, x, y, z, scalar)
    ble = np.empty(3, dtype=np.ndarray)
    ble[0] = np.empty(0, dtype=np.float64)    # timestamp
    ble[1] = np.empty(0, dtype=str)           # MAC address
    ble[2] = np.empty(0, dtype=np.int8)       # RSSI (>= -128)

    print(f"loading {path.basename(file)}")

    with open(file) as f:
        for row in csv.reader(f, delimiter="\t"):
            for i, s in enumerate(INERTIAL_SENSORS):
                if s == row[1]:
                    inertial[i] = np.vstack((inertial[i], (np.float64(row[0]), *[np.float64(v) for v in row[2].split(",")[1:]])))
                    break

            if ENABLE_BLE and row[1] == "BLE":
                row_2 = row[2].split(",")
                ble[0] = np.hstack((ble[0], np.float64(row[0])))
                ble[1] = np.hstack((ble[1], row_2[0].lower()))
                ble[2] = np.hstack((ble[2], np.int8(row_2[1])))

    print(f"{path.basename(file)} has been loaded")

    return inertial, ble

def _resample_inertial_log(data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    resampled_ts = np.arange(max(d[0, 0] for d in data), min(d[-1, 0] for d in data), step=1/FREQ, dtype=np.float64)
    resampled_val = np.empty((len(resampled_ts), 3 * len(INERTIAL_SENSORS) + 1 if "ROTV" in INERTIAL_SENSORS else 3 * len(INERTIAL_SENSORS)), dtype=np.float64)

    col_index = 0
    for sensor_index, s in enumerate(INERTIAL_SENSORS):
        if s in ("ACC", "GRAV", "GYRO", "MAG"):
            val_len = 3
        elif s == "ROTV":
            val_len = 4
        for i in range(val_len):
            resampled_val[:, col_index + i] = interp1d(data[sensor_index][:, 0], data[sensor_index][:, i + 1])(resampled_ts)
        col_index += val_len

    return resampled_ts, resampled_val

def _unix2datetime(ts: np.ndarray) -> np.ndarray:
    ts = ts.astype(object)    # enable to store datetime

    for i, t in enumerate(ts):
        ts[i] = datetime.fromtimestamp(t)

    return ts.astype(datetime)

def _format_log(src_file: str, tgt_dir: str, label: Optional[str]) -> None:
    inertial, ble = _load_log(src_file)
    
    resampled_ts, resampled_val = _resample_inertial_log(inertial)
    resampled_ts = _unix2datetime(resampled_ts)

    # inertial
    dir = path.join(tgt_dir, "inertial/")
    if not path.exists(dir):
        mkdir(dir)
    inertial_tgt_file_name = path.splitext(path.basename(src_file))[0] + "_inertial_" + "".join(s[0].lower() for s in INERTIAL_SENSORS) + ("" if label is None else "_" + label)
    tgt_file = path.join(dir, inertial_tgt_file_name + ".csv")
    with open(tgt_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        t: datetime
        for i, t in enumerate(resampled_ts):
            writer.writerow((t.strftime("%Y-%m-%d %H:%M:%S.%f"), *resampled_val[i]))

    print(f"written to inertial/{path.basename(tgt_file)}")

    tgt_file = path.join(dir, inertial_tgt_file_name + ".pkl")
    with open(tgt_file, mode="wb") as f:
        pickle.dump((resampled_ts, resampled_val), f)
    
    print(f"written to inertial/{path.basename(tgt_file)}")

    # ble
    if ENABLE_BLE:
        ble[0] = _unix2datetime(ble[0])

        dir = path.join(tgt_dir, "ble/")
        if not path.exists(dir):
            mkdir(dir)
        tgt_file = path.join(dir, path.splitext(path.basename(src_file))[0] + "_ble" + ("" if label is None else "_" + label) + ".csv")
        with open(tgt_file, mode="w", newline="") as f:
            writer = csv.writer(f)
            t: datetime
            for i, t in enumerate(ble[0]):
                writer.writerow((t.strftime("%Y-%m-%d %H:%M:%S.%f"), ble[1][i], ble[2][i]))

        print(f"written to ble/{path.basename(tgt_file)}")

def format_logs(src_file: Optional[str] = None, src_dir: Optional[str] = None, tgt_dir: Optional[str] = None, label: Optional[str] = None) -> None:
    if tgt_dir is None:
        tgt_dir = path.join(ROOT_DIR, "formatted/")    # save to default target directory

    if src_file is None and src_dir is None:
        for src_file in iglob(path.join(ROOT_DIR, "raw/*.log")):    # loop for default source directory
            _format_log(src_file, tgt_dir, label)

    elif src_file is None:
        for src_file in iglob(path.join(src_dir, "*.log")):    # loop for specified source directory
            _format_log(src_file, tgt_dir, label)

    elif src_dir is None:
        _format_log(src_file, tgt_dir, label)

    else:
        raise Exception("'src_file' and 'src_dir' are specified at the same time")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf_file", help="specify config file", metavar="PATH_TO_CONF_FILE")
    parser.add_argument("--src_file", help="specify source file", metavar="PATH_TO_SRC_FILE")
    parser.add_argument("--src_dir", help="specify source directory", metavar="PATH_TO_SRC_DIR")
    parser.add_argument("--tgt_dir", help="specify target directory", metavar="PATH_TO_TGT_DIR")
    parser.add_argument("-l", "--label", help="specify label", metavar="LABEL")
    args = parser.parse_args()

    _set_params(args.conf_file)

    format_logs(args.src_file, args.src_dir, args.tgt_dir, args.label)
