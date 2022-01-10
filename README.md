# hasc_log_formatter.py
This is Python module to resample frequency and convert logs format from LOG exported by [HASC Logger](https://github.com/UCLabNU/HASC_Logger_Android) to CSV able to be interpreted by [particle_filter.py](https://github.com/kazumakano/particle_filter.py) and [simple_pdr.py](https://github.com/kazumakano/simple_pdr.py).

# Usage
You can run this formatter as following.
You can specify config file, source file or directory and target directory with flags.
`config/default.yaml` will be used if no config file is specified.
Default source and target directory are `raw/` and `formatted/`.
```sh
python script/format_logs.py [--conf_file PATH_TO_CONF_FILE] [--src_file PATH_TO_SRC_FILE] [--src_dir PATH_TO_SRC_DIR] [--tgt_dir PATH_TO_TGT_DIR]
```
