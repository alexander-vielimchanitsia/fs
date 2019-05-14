import argparse

from fat import cli


def main():
    parser = argparse.ArgumentParser()
    add = parser.add_argument

    add('action', choices=['mkdir', 'touch', 'write', 'read'])
    add('path_name', help='path of a file or directory for an action')
    add('--data', help='data for `write` action')

    cmd = parser.parse_args()

    args = [cmd.path_name]
    if cmd.data:
        args.append(cmd.data)
    getattr(cli, cmd.action)(*args)


if __name__ == '__main__':
    main()
