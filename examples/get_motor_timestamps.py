import sys
import numpy as np
from datetime import datetime

def load_data(filename):
    with open(filename, 'r') as f:
        raw_lines = f.readlines()
    data_lines = []
    for line in raw_lines[1:]:
        line = line.strip()
        line = line.split(',')
        data_lines.append(line)
    return data_lines

def timestamps_from_data(data_lines):
    dt = [datetime.strptime(x[0],'%Y-%m-%d %H:%M:%S.%f') for x in data_lines]
    t_stamps = np.array([x.timestamp() for x in dt])
    return t_stamps


# ----------------------------------------------------------------------------
if __name__ == '__main__':

    filename = sys.argv[1]

    data = load_data(filename)
    t_stamps = timestamps_from_data(data)
    np.savetxt('t_stamps.txt', t_stamps)





