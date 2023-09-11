import argparse
import sequence
import sys
import logging

import sequence.static

parser = argparse.ArgumentParser(description='Sequence command-line utility')
subparsers = parser.add_subparsers(dest='command', required=True)

verbose_args = ('-v', '--verbose')
verbose_kwargs = dict(
    help='Verbose output (puts loggers in debug mode)',
    action='store_true'
)

param_args = ('-p', '--parameter')
param_kwargs = dict(
    action='append',
    nargs=2,
    metavar=('name', 'value'),
    help='Sets a parameter'
)

run_parser: argparse.ArgumentParser = subparsers.add_parser('run', help='Run a sequence')
run_parser.add_argument('url')
run_parser.add_argument(*param_args, **param_kwargs)
run_parser.add_argument(*verbose_args, **verbose_kwargs)

test_parser: argparse.ArgumentParser = subparsers.add_parser('test', help='Test a sequence')
test_parser.add_argument('url')
test_parser.add_argument(*param_args, **param_kwargs)
test_parser.add_argument(*verbose_args, **verbose_kwargs)


def run(url: str, parameters: dict):
    from sequence.visitors.run import SequenceFrame
    seq = sequence.load(url)
    root_frame = SequenceFrame(parameters=parameters)
    root_frame.visit(seq)
    sequence.static.logger.info(f"Stack at end-of-sequence: {root_frame.stack}")


def test(url: str, parameters: dict):
    from sequence.visitors.tester import SequenceTester
    seq = sequence.load(url)
    tester = SequenceTester(parameters=parameters)
    tester.visit(seq)
    sequence.static.logger.info("Test passed")


def main():
    args = parser.parse_args(sys.argv[1:])
    parameters = {p[0]: p[1] for p in args.parameter} if args.parameter else {}
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    if args.command == 'test':
        func = test
    elif args.command == 'run':
        func = run
    else:
        raise ValueError("invalid command")
    func(args.url, parameters)
