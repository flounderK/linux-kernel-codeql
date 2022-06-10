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
                        default="all_struct_fields_no_fieldsize.csv")
    parser.add_argument("-ne", "--no-expand", action='store_true',
                        default=False)
    parser.add_argument("-no", "--no-offsets", action='store_true',
                        default=False)
    parser.add_argument("-l", "--list", help="List out valid struct names",
                        action='store_true', default=False)
    parser.add_argument("--all", help="print all structs", action='store_true',
                        default=False)

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

        set_default_fieldsize = False

        if 'fieldsize' not in colnames:
            colnames.append('fieldsize')
            set_default_fieldsize = True

        Row = namedtuple("Row", colnames)

        # Hack to add a fieldsize value, even if it wasn't
        # actually in the csv
        if set_default_fieldsize:
            Row.__new__.__defaults__ = (0,)

        contents.append(Row(*first_row))

        # set the values in the csv to their expected types,
        # creating new rows
        for row in csvreader:
            contents.append(Row(*[a(b) for a, b in zip(casts, row)]))
        return contents


def group_struct_fields(struct_fields):
    """
    Group structs by struct name and struct size,
    deduping duplicate fields. Return a mapping of structs by  a tuple of
    (structname, structsize) => [..., struct fields, ...]
    """
    # Group structs by struct name and struct size, deduping duplicate fields.
    structsets = defaultdict(set)
    for s in struct_fields:
        structsets[(s.structname, s.structsize)].add(s)

    grouped_structs = [list(i) for i in structsets.values()]
    # sort fields by field offset
    grouped_structs = [sorted(i, key=lambda a: a.offset) for i in grouped_structs]

    fixed_grouped_structs = []
    for structfields in grouped_structs:
        fixed_structfields = []
        structfields_len = len(structfields)

        # skip this if fieldsize is actually populated
        if any([field.fieldsize for field in structfields]):
            fixed_structfields = structfields
            fixed_grouped_structs.append(fixed_structfields)
            continue

        if structfields_len == 1:
            new_fields = structfields[0]._replace(fieldsize=structfields[0].structsize)
            fixed_structfields.append(new_fields)
            fixed_grouped_structs.append(fixed_structfields)
            continue

        for ind in range(0, structfields_len-1):
            field = structfields[ind]
            next_field = structfields[ind+1]
            field_size = next_field.offset - field.offset
            fixed_structfields.append(field._replace(fieldsize=field_size))

        last_fieldsize = next_field.structsize - next_field.offset
        fixed_structfields.append(next_field._replace(fieldsize=last_fieldsize))

        fixed_grouped_structs.append(fixed_structfields)

    # then store by structname
    structs = {}
    for s in fixed_grouped_structs:
        structs[StructTuple(s[0].structname, s[0].structsize)] = s
    return structs


class StructFormatter:
    def __init__(self, structs, expand=True, offsets=True,
                 single_tab='  '):
        self.structs = structs
        self.expand = expand
        self.offsets = offsets
        self.single_tab = single_tab

        if self.offsets:
            self.struct_format = "%5d: %sstruct %s {\n%s%5d: %s}"
            self.field_format = "%5d: %s%s%s %s;\n"
        else:
            self.field_format = "%s%s%s %s;\n"
            self.struct_format = "%sstruct %s {\n%s%s}"

    def get_structs_by_name(self, name):
        return [i for i in list(self.structs.keys())
                if i.structname == name]

    def format_struct(self, struct_key, tabs='', offset=0):
        # tabs, structname, fields
        # tabs, single_tab, field type, field name
        fields = ''
        for field in self.structs[struct_key]:
            maybe_struct_type = StructTuple(field.type, field.fieldsize)
            maybe_struct_type_fields = self.structs.get(maybe_struct_type)
            # handle embedded struct format
            if self.expand is True and \
               maybe_struct_type_fields is not None \
               and field.type.find('<unnamed>') == -1:
                fields += self.format_struct(maybe_struct_type,
                                             tabs + self.single_tab,
                                             offset + field.offset)
                fields += ' %s;\n\n' % field.fieldname
            else:
                if self.offsets:
                    field_tuple = (offset + field.offset,
                                   tabs, self.single_tab,
                                   field.type,
                                   field.fieldname)
                else:
                    field_tuple = (tabs, self.single_tab,
                                   field.type,
                                   field.fieldname)
                fields += self.field_format % field_tuple

        if self.offsets:
            struct_tuple = (offset, tabs,
                            struct_key.structname, fields,
                            offset + struct_key.structsize, tabs)
        else:
            struct_tuple = (tabs, struct_key.structname, fields, tabs)
        full_format = self.struct_format % struct_tuple

        return full_format

    def print_struct_by_name(self, name):
        for struct in self.get_structs_by_name(name):
            print(self.format_struct(struct))
            print()


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    contents = get_contents(args.csv)
    structs = group_struct_fields(contents)
    sf = StructFormatter(structs, expand=not args.no_expand,
                         offsets=not args.no_offsets)

    if args.list:
        for struct, fields in structs.items():
            print(struct.structname)
    elif args.all:
        for struct in structs.keys():
            sf.print_struct_by_name(struct.structname)
    else:
        sf.print_struct_by_name(args.structname)
