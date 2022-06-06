#!/usr/bin/env python3
import argparse
import sys
import csv
import re
from collections import namedtuple, defaultdict

StructTuple = namedtuple("StructTuple", ['structname', 'structsize'])


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--structname", help="Name of struct to print")
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


def group_struct_fields(struct_fields):
    # group structs by struct name and struct size, deduping duplicate fields
    structsets = defaultdict(set)
    for s in struct_fields:
        structsets[(s.structname, s.structsize)].add(s)

    grouped_structs = [list(i) for i in structsets.values()]
    grouped_structs = [sorted(i, key=lambda a: a.offset) for i in grouped_structs]

    # then store by structname
    structs = {}
    for s in grouped_structs:
        structs[StructTuple(s[0].structname, s[0].structsize)] = s
    return structs


def get_structs_by_name(structs, name):
    return [i for i in list(structs.keys()) if i.structname == name]


def format_struct(structs, struct_key, tabs='', single_tab='  '):
    # tabs, structname, fields
    struct_format = "%sstruct %s {\n%s%s}"
    # tabs, single_tab, field type, field name
    field_format = "%s%s%s %s;\n"
    fields = ''
    for field in structs[struct_key]:
        maybe_struct_type = StructTuple(field.type, field.fieldsize)
        maybe_struct_type_fields = structs.get(maybe_struct_type)
        if maybe_struct_type_fields is not None \
                    and field.type.find('<unnamed>') == -1:
            fields += format_struct(structs, maybe_struct_type,
                                    tabs + single_tab,
                                    single_tab)
            fields += ' %s;\n\n' % field.fieldname
        else:
            fields += field_format % (tabs, single_tab,
                                      field.type,
                                      field.fieldname)

    full_format = struct_format % (tabs,
                                   struct_key.structname,
                                   fields, tabs)

    return full_format



if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    contents = get_contents(args.csv)
    structs = group_struct_fields(contents)

    target_name = 'apple_sc_backlight'



