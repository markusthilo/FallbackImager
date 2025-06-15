# SQL2CSV

Python script to fill a SQLite DB file by SQL dump and write content as CSV.

## Features

- Execute SQL statements directly or from files
- Convert SQL dumps to SQLite-compatible format
- Export tables to CSV files
- View database schema
- Extract specific columns or tables
- Customize output format with delimiters

## Usage

```
sql2csv.py [-h] [-a DIRECTORY] [-c COLUMN NAME / STRING] [-d CHAR / STRING]
           [-e SQL STATEMENT / STRING] [-f SQL FILE] [-g] [-l] [-n INTEGER]
           [-r PATH] [-s] [-t TABLE NAME / STRING] [-w FILE]
           FILE
```

### Arguments

- `FILE`: SQLite database file path

### Options

- `-a, --all DIRECTORY`: Export all tables to CSV files in the specified directory
- `-c, --column COLUMN`: Select a specific column (requires `-t/--table`)
- `-d, --delimiter CHAR`: Set delimiter between columns (default: tab)
- `-e, --execute SQL`: Execute SQL statement
- `-f, --file PATH`: Execute SQL statements from file with SQLite compatibility translation
- `-g, --debug`: Enable debug mode
- `-l, --headless`: Omit headers/field names in output
- `-n, --lines INTEGER`: Limit output to n lines (0 for headers only)
- `-r, --read PATH`: Execute SQL statements from file without translation
- `-s, --schema`: Print database schema
- `-t, --table TABLE`: Select table to export
- `-w, --write FILE`: Write output to file instead of stdout

## Examples

### Execute SQL statement
```
python sql2csv.py sqlite.db -e "SELECT * FROM table_name"
```

### Import SQL dump with SQLite compatibility
```
python sql2csv.py database.db -f dump.sql
```

### View database schema
```
python sql2csv.py sqlite.db -s
```

### Export a table to CSV
```
python sql2csv.py sqlite.db -t table_name -w outfile.csv
```

### Export a specific column
```
python sql2csv.py sqlite.db -t table_name -c column_name -w outfile.csv
```

### Export all tables to separate CSV files
```
python sql2csv.py sqlite.db -a ./exports
```

## Classes and Functions

### SqliteDb
Handles SQLite database operations:
- `get_tables()`: Lists all tables in the database
- `get_columns(table)`: Lists columns in a table
- `count_rows(table)`: Counts rows in a table
- `fetch_table(table)`: Retrieves all rows from a table
- `fetch_column(table, column)`: Retrieves values from a specific column
- `get_type(table, column)`: Determines data type of a column

### SqlFile
Reads SQL statements from files:
- `read()`: Parses SQL statements from file

### Translator
Extends SqlFile to make SQL dumps compatible with SQLite:
- `read()`: Removes incompatible SQL syntax

### Worker
Main class that performs operations:
- `execute(statement)`: Executes SQL statement
- `execute_file(sql_path, raw)`: Executes SQL from file
- `schema()`: Prints database schema
- `table(table)`: Exports table to CSV
- `column(table, column)`: Exports column to CSV
- `dump_all(dir_path)`: Exports all tables to CSV files

## Legal Notice

### License
Respect GPL-3: https://www.gnu.org/licenses/gpl-3.0.en.html

### Disclaimer
Use the software on your own risk.

This is not a commercial product with an army of developers and a department for quality control behind it.
