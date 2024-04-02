#!/bin/bash

# Before Running the Test:
#  - Start IBGateway and verify correct configurations
# Run Parameters:
#  - bar size: 1 Day
#  - duration: 2 Weeks
#  - end date: 2023-12-12
#  - end time: 08:15:00
#  - debug mode: true
#  - output file: aapl_1d_2w_2023_12_12_08:15:00.csv
scout historical-quote aapl -br "1 Day" -dr "2 W" -ed "2023-12-12" -et "08:15:00" -b -o "aapl_1d_2w_2023_12_12_08:15:00.csv"
