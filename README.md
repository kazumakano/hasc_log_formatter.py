# hasc_log_formatter.py
This is Python module to resample frequency and convert logs format from LOG exported by [HASC Logger](https://github.com/UCLabNU/HASC_Logger_Android) to CSV able to be interpreted by [pdr.py](https://github.com/kazumakano/pdr.py) and [particle_filter.py](https://github.com/kazumakano/particle_filter.py).

# Usage
You can run this formatter as following.
You can specify config file, source file or directory and target directory with flags.
Default source and target directory are `raw/` and `formatted/`.
```sh
python script/format_logs.py [--config PATH_TO_CONFIG_FILE] [--src_file PATH_TO_SRC_FILE] [--src_dir PATH_TO_SRC_DIR] [--tgt_dir PATH_TO_TGT_DIR]
```
