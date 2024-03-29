#!/usr/bin/env python3
import argparse
import os
import sys
import pathlib


def run_make(args):

    if args.build_dir.startswith('/'):
        build_dir = args.build_dir
    else:
        build_dir = os.path.join(args.linux_repo_dir, args.build_dir)

    for p in [args.codeql_db_dir, build_dir]:
        directory = pathlib.Path(p)
        directory.mkdir(parents=True, exist_ok=True)

    codeql_linux_db_dir = os.path.join(args.codeql_db_dir,
                                       args.db_name)

    # export output directory for build
    os.environ['KBUILD_OUTPUT'] = build_dir

    if not args.dry_run and args.clean:
        os.system(f"make -C {args.linux_repo_dir} distclean")

    if not args.dry_run and not args.skip_make_defconfig and not args.skip_database_create:
        os.system(f"make -C {args.linux_repo_dir} defconfig")

    codeql_make_cmd_args = ["codeql",
                            "database",
                            "create",
                            f"'{codeql_linux_db_dir}'",
                            f"--search-path='{args.codeql_repo_dir}'",
                            "--language=cpp",
                            "-s", f"'{args.linux_repo_dir}'",
                            "-c", f"'{args.cmd}'",
                            "--overwrite"]
    codeql_make_cmd = ' '.join(codeql_make_cmd_args)

    print(f"codeql create cmd \"{codeql_make_cmd}\"")
    if not args.dry_run and not args.skip_database_create:
        os.system(codeql_make_cmd)

    # it apears that codeql database analyze is not entirely necessary
    # codeql_analyze_cmd_args = ["codeql",
    #                            "database",
    #                            "analyze",
    #                            f"--search-path='{args.codeql_repo_dir}'",
    #                            f"'{codeql_linux_db_dir}'"]

    # codeql_analyze_cmd = ' '.join(codeql_analyze_cmd_args)
    # print(f"codeql analyze \"{codeql_analyze_cmd}\"")
    # if not args.dry_run and not args.skip_database_analyze:
    #     os.system(codeql_analyze_cmd)


def valid_args_and_environment(args):
    codeql_is_missing = bool(os.system("command -v codeql"))
    if codeql_is_missing:
        print("codeql not found on $PATH")
        return False

    for p in [args.linux_repo_dir, args.codeql_repo_dir]:
        if not os.path.exists(p):
            print(f"{p} does not exist")
            return False
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--linux-repo-dir",
                        help="path to linux source code repo",
                        type=os.path.expanduser,
                        default=os.path.expanduser("~/cloned/linux"))

    parser.add_argument("-cq", "--codeql-repo-dir",
                        help="path to codeql repo",
                        type=os.path.expanduser,
                        default=os.path.expanduser("~/cloned/codeql"))
    parser.add_argument("-b", "--build-dir",
                        type=os.path.expanduser,
                        default="codeql_build",
                        help="path of build directory")

    parser.add_argument("-cd", "--codeql-db-dir",
                        type=os.path.expanduser,
                        default=os.path.expanduser("~/Documents/codeql_dbs"))
    parser.add_argument("-db", "--db-name", default="linux_cqldb",
                        help="Name of linux codeql db")
    parser.add_argument("-sd", "--skip-make-defconfig", action="store_true",
                        default=False,
                        help="skip 'make defconfig' and assume that the "
                        "repo is already correctly set up")
    parser.add_argument("-c", "--cmd", default='make',
                        help="command to pass to codeql to build the source")
    parser.add_argument("-sdc", "--skip-database-create", default=False,
                        action="store_true",
                        help="don't run database creation")
    parser.add_argument("-sda", "--skip-database-analyze", default=False,
                        action="store_true",
                        help="don't run database analyze")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="don't actually run final commands")
    parser.add_argument("--clean", action="store_true", default=False,
                        help="run make clean first")

    args = parser.parse_args()
    if not valid_args_and_environment(args):
        sys.exit(-1)
    run_make(args)
