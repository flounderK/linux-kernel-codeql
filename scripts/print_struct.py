#!/usr/bin/env python3
import argparse
import sys
import csv
import re
from collections import namedtuple


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("structname", help="Name of struct to print")
    parser.add_argument("-c", "--csv", help="Path of csv file",
                        default="all_struct_fields.csv")
    args = parser.parse_args(argv)
    return args


def get_contents(file):
    with open(file, "r") as f:
        contents = []
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        csvreader = csv.reader(f, dialect)
        colnames = next(csvreader)
        sample = next(csvreader)
        casts = []
        first_row = []
        int_rexp = re.compile(r'-?\d+')
        # try to identify column types
        for key, val in zip(colnames, sample):
            if re.match(int_rexp, val) is not None:
                casts.append(int)
                first_row.append(int(val))
            else:
                first_row.append(val)
                casts.append(str)

        Row = namedtuple("Row", colnames)

        contents.append(Row(*first_row))

        for row in csvreader:
            contents.append(Row(*[a(b) for a, b in zip(casts, row)]))
        return contents


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    contents = get_contents(args.csv)
