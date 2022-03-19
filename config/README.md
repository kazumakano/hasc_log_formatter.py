# config
This is directory for config files.
Put your config files here.
Config file must contain following parameters:
| Key              | Description                     | Notes                                           | Type        |
| ---              | ---                             | ---                                             | ---         |
| enable_ble       | format ble logs or not          |                                                 | `bool`      |
| freq             | frequency of inertial logs [Hz] |                                                 | `float`     |
| inertial_sensors | list of inertial sensor tags    | 'ACC', 'GRAV', 'GYRO', and 'ROTV' are supported | `list[str]` |
