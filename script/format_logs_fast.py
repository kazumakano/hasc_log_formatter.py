import csv
import os.path as path
import pickle
from datetime import datetime
from glob import iglob
from os import mkdir
from typing import Optional
import joblib
import numpy as np
import yaml
from scipy.interpolate import interp1d

JOB_NUM = -1

def _resample_inertial_data(data: list[np.ndarray], freq: float) -> tuple[np.ndarray, np.ndarray]:
    resampled_ts = np.arange(max(d[0, 0] for d in data), min(d[-1, 0] for d in data), step=1 / freq, dtype=np.float64)
    resampled_val = np.empty((len(resampled_ts), sum(d.shape[1] - 1 for d in data)), dtype=np.float64)

    col_idx = 0
    for d in data:
        for i in range(1, d.shape[1]):
            resampled_val[:, col_idx] = interp1d(d[:, 0], d[:, i])(resampled_ts)
            col_idx += 1

    return resampled_ts, resampled_val

def _unix2datetime(ts: np.ndarray) -> np.ndarray:
    ts = ts.astype(object)

    for i, t in enumerate(ts):
        ts[i] = datetime.fromtimestamp(t)

    return ts.astype(datetime)

def _write_inertial_data(tgt_dir: str, tgt_file_name: str, ts: np.ndarray, val: np.ndarray) -> None:
    if not path.exists(tgt_dir):
        mkdir(tgt_dir)

    with open(path.join(tgt_dir, tgt_file_name + ".csv"), mode="w", newline="") as f:
        writer = csv.writer(f)
        t: datetime
        for i, t in enumerate(ts):
            writer.writerow((t.strftime("%Y-%m-%d %H:%M:%S.%f"), *val[i]))

    with open(path.join(tgt_dir, tgt_file_name + ".pkl"), mode="wb") as f:
        pickle.dump((ts, val), f)

def _write_radio_data(tgt_dir: str, tgt_file_name: str, ts: np.ndarray, mac: np.ndarray, rssi: np.ndarray) -> None:
    if not path.exists(tgt_dir):
        mkdir(tgt_dir)

    with open(path.join(tgt_dir, tgt_file_name + ".csv"), mode="w", newline="") as f:
        writer = csv.writer(f)
        t: datetime
        for i, t in enumerate(ts):
            writer.writerow((t.strftime("%Y-%m-%d %H:%M:%S.%f"), mac[i], rssi[i]))

    with open(path.join(tgt_dir, tgt_file_name + ".pkl"), mode="wb") as f:
        pickle.dump((ts, mac, rssi), f)

def _format_log(conf: dict[str, bool | float | list[str]], src_file: str, tgt_dir: str, label: str | None) -> None:
    inertial_data = [[] for _ in conf["inertial_sensors"]]
    if conf["enable_ble"]:
        ble_data = ([], [], [])
    if conf["enable_wifi"]:
        wifi_data = ([], [], [])

    with open(src_file) as f:
        for row in csv.reader(f, delimiter="\t"):
            if row[1] in conf["inertial_sensors"]:
                inertial_data[conf["inertial_sensors"].index(row[1])].append((float(row[0]), *[float(v) for v in row[2].split(",")[1:]]))
            elif conf["enable_ble"] and row[1] == "BLE":
                row_2 = row[2].split(",")
                ble_data[0].append(float(row[0]))
                ble_data[1].append(row_2[0].lower())
                ble_data[2].append(int(row_2[1]))
            elif conf["enable_wifi"] and row[1] == "WIFI":
                row_2 = row[2].split(",")
                for c in row_2:
                    c = c.split("|")
                    if len(c) == 3:
                        wifi_data[0].append(float(row[0]))
                        wifi_data[1].append(c[0].lower())
                        wifi_data[2].append(int(c[2]))

    if len(conf["inertial_sensors"]) > 0:
        inertial_ts, inertial_val = _resample_inertial_data([np.array(l, dtype=np.float64) for l in inertial_data], conf["freq"])
        _write_inertial_data(
            path.join(tgt_dir, "inertial/"),
            path.splitext(path.basename(src_file))[0] + ("" if label is None else "_" + label) + "_inertial_" + "".join(s[0].lower() for s in conf["inertial_sensors"]),
            _unix2datetime(inertial_ts),
            inertial_val
        )

    if conf["enable_ble"]:
        _write_radio_data(
            path.join(tgt_dir, "ble/"),
            path.splitext(path.basename(src_file))[0] + ("" if label is None else "_" + label) + "_ble",
            _unix2datetime(np.array(ble_data[0], dtype=np.float64)),
            np.array(ble_data[1], dtype="<U17"),
            np.array(ble_data[2], dtype=np.int32)
        )

    if conf["enable_wifi"]:
        _write_radio_data(
            path.join(tgt_dir, "wifi/"),
            path.splitext(path.basename(src_file))[0] + ("" if label is None else "_" + label) + "_wifi",
            _unix2datetime(np.array(wifi_data[0], dtype=np.float64)),
            np.array(wifi_data[1], dtype="<U17"),
            np.array(wifi_data[2], dtype=np.int32)
        )

def format_logs(conf_file: Optional[str] = None, src_file: Optional[str] = None, src_dir: Optional[str] = None, tgt_dir: Optional[str] = None, label: Optional[str] = None) -> None:
    with open(path.join(path.dirname(__file__), "../config/default.yaml") if conf_file is None else conf_file) as f:
        conf = yaml.safe_load(f)

    if tgt_dir is None:
        tgt_dir = path.join(path.dirname(__file__), "../formatted/")

    if src_file is None and src_dir is None:
        with joblib.Parallel(n_jobs=JOB_NUM) as p:
            p(joblib.delayed(_format_log)(conf, f, tgt_dir, label) for f in iglob(path.join(path.dirname(__file__), "../raw/*.log")))

    elif src_file is None:
        with joblib.Parallel(n_jobs=JOB_NUM) as p:
            p(joblib.delayed(_format_log)(conf, f, tgt_dir, label) for f in iglob(path.join(src_dir, "*.log")))

    elif src_dir is None:
        _format_log(conf, src_file, tgt_dir, label)

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

    format_logs(args.conf_file, args.src_file, args.src_dir, args.tgt_dir, args.label)
