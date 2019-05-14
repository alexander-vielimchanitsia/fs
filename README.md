# fs
Simple file-system implementations

## Usage

Setup:

    $ make install

Run tests:

    $ make test

### FAT

    $ make fat mkdir /foo
    $ make fat mkdir /foo/bar
    $ make fat touch /foo/bar/test.txt
    $ make fat write /foo/bar/test.txt data="some test data"
    $ make fat read /foo/bar/test.txt
    some test data
