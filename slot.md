# Click Board Slot Configuration

This document maps each click board slot to its corresponding BeagleBone GPIO pins and assigned modules.

## Slot Assignments

| Slot | Pin Assignment | Modules |
|------|----------------|---------|
| 1 | P9_15 (GPIO Input), P9_14 (PWM), P9_38 (ADC) | Motion Sensor, VibroMotor, IR Distance |
| 2 | P9_41 (GPIO Input), P9_23 (GPIO Output), P9_37 (ADC) | VibraSense, Flame Sensor |
| 3 | P8_19 (PWM), P9_40 (ADC) | Buzzer, Microphone |
| 4 | P8_10 (GPIO Input), P9_39 (ADC) | Reed Switch, Force Sensor |

## Module to Slot Mapping

| Module | Slot | Pin Type | Pin |
|--------|------|----------|-----|
| Motion Sensor | 1 | GPIO Input | P9_15 |
| VibroMotor | 1 | PWM | P9_14 |
| IR Distance | 1 | ADC | P9_38 |
| VibraSense | 2 | GPIO Input/Output | P9_41 / P9_23 |
| Flame Sensor | 2 | ADC | P9_37 |
| Buzzer | 3 | PWM | P8_19 |
| Microphone | 3 | ADC | P9_40 |
| Reed Switch | 4 | GPIO Input | P8_10 |
| Force Sensor | 4 | ADC | P9_39 |

