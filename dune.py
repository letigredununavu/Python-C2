import argparse
from tcp_server import TCPServer
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

    '''
    parser.add_argument(
        "-i", "--interface",
        default="0.0.0.0",
        help="Set the listening interface for incoming connections (default: 0.0.0.0)"
    )

    parser.add_argument(
        "-p", "--port",
        default="8888",
        type=int,
        help="Port on which to listen for incoming connections (default: 8888)"
    )
    '''

    return parser.parse_args()

def main():
    args = parse_arguments()
    log = logger.Logger(verbosity=args.verbosity)
    log.info(f"Verbosity level is at : {args.verbosity}")
    cmd = ArakisCLI(args.verbosity)
    cmd.cmdloop()


if __name__ == '__main__':
    main()

