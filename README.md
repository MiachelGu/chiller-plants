# Analysis of Kaer's Chiller Plants

## Notes

- CWSHDR gives good results with two layers
- The stored models (h5 files) are system dependent. 
    cwshdr1.h5 works on Catan and other on ADSC.

## Models
    cwshdr2.h5
    Features: ["loadsys", "drybulb", "rh", "cwrhdr", "cwsfhdr"]
    Target: ["cwshdr"]
    Lookback: 15

    cwshdr3.h5
    Features: ["loadsys", "drybulb", "rh", "cwrhdr", "cwsfhdr"]
    Target: ["cwshdr"]
    Lookback: 15
    Distillation. 75-150-150

## Setup Notes
    FastDTW falls back to pure Python and doesn't. Execute `python setup.py build` 
    and see whether the build is executed successfully. On Windows, need to run
        Ref to fix Windows: https://stackoverflow.com/questions/43847542/
        Ref to fix Linux: < need to figure out >

## Dashboard

Check /dashboard/readme.txt for more information

![Dashboard Screenshot](/output/dashboard1.png?raw=true "Dynamic View")
![Dashboard Screenshot](/output/dashboard2.png?raw=true "Monthly View")
