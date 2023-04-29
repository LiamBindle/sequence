import argparse
import json
import zvm


def main():
    parser = argparse.ArgumentParser(description='Run a routine')
    parser.add_argument('file', type=str, help='Path to routine')
    parser.add_argument('-t', '--test', action='store_true', help='Run routine tests')
    args = parser.parse_args()

    with open(args.file, 'r') as f:
        routine = json.load(f)

    if args.test:
        zvm.run_test(routine)
    else:
        zvm.run(routine)
