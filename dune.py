import argparse
import logger
from arakis import ArakisCLI

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Sandworm pyhton C2 argument's parser")

    parser.add_argument(
        "-v", "--verbosity",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Set the verbosity level (default: info)"
    )

    return parser.parse_args()

def main():
    args = parse_arguments()
    log = logger.Logger(verbosity=args.verbosity)
    cmd = ArakisCLI(args.verbosity)
    cmd.cmdloop()


if __name__ == '__main__':
    main()

