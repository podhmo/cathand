help
```console
handofcats dump.py:run -h
usage: handofcats [-h] [--expose] [--format {json,csv}]

optional arguments:
  -h, --help           show this help message and exit
  --expose
  --format {json,csv}  (default: 'json')
```
run
```console
handofcats dump.py:run
[
  {
    "name": "foo",
    "age": 20
  },
  {
    "name": "bar",
    "age": 21
  }
]
handofcats dump.py:run --format=csv
name,age
foo,20
bar,21
```
--expose
```console
handofcats dump.py:run --expose | tee dump-exposed.py
import sys
import typing as t


def csv_dump(rows: t.Sequence[dict]) -> None:
    import csv
    w = csv.DictWriter(sys.stdout, ["name", "age"])
    w.writeheader()
    w.writerows(rows)


def json_dump(rows: t.Sequence[dict]) -> None:
    import json
    json.dump(rows, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


DumpFormat = t.NewType("DumpFormat", str)
DumpFormat.choices = ["json", "csv"]


def run(*, format: DumpFormat = "json"):
    rows = [
        {
            "name": "foo",
            "age": 20,
        },
        {
            "name": "bar",
            "age": 21,
        },
    ]
    dump = globals()["{}_dump".format(format)]
    dump(rows)

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=None)
    parser.print_usage = parser.print_help
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help="(default: 'json')", required=False)
    args = parser.parse_args(argv)
    run(**vars(args))


if __name__ == '__main__':
    main()
```