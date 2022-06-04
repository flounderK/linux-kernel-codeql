codeql query run --search-path="$HOME/cloned/codeql" -d "$HOME/Documents/codeql_dbs/linux_cqldb" linuxqlpack/all_struct_fields.ql --output=all_struct_fields.bqrs
codeql bqrs decode all_struct_fields.bqrs -k 0,1,4 --format=csv -o all_struct_fields.csv
