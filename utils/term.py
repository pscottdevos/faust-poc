import asyncio
import atexit
import sys
from termios import *


# Indexes for termios list.
IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

def setraw(fd, when=TCSAFLUSH):
    """Put terminal into a raw mode."""
    mode = tcgetattr(fd)
    mode[IFLAG] = mode[IFLAG] & ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON)
    #mode[OFLAG] = mode[OFLAG] & ~(OPOST)
    mode[CFLAG] = mode[CFLAG] & ~(CSIZE | PARENB)
    mode[CFLAG] = mode[CFLAG] | CS8
    mode[LFLAG] = mode[LFLAG] & ~(ECHO | ICANON | IEXTEN | ISIG)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)


def get_term_reader_protocol(on_data_received=lambda d: d, set_echo_enabled=False):

    class TermReaderProtocol(asyncio.Protocol):
        
        def __init__(self, *args, **kwargs):
            self.configure(set_echo_enabled)
            super().__init__(*args, **kwargs)

        @staticmethod
        def configure(set_echo_enabled=False):
            fd = sys.stdin.fileno()
            default_mode = tcgetattr(fd)
            atexit.register(tcsetattr, fd, TCSADRAIN, default_mode)
            mode = tcgetattr(fd)
            if set_echo_enabled:
                mode[LFLAG] |= ECHO
            else:
                mode[LFLAG] &= ~ECHO
            setraw(fd)

        def connection_made(self, transport):
            print('pipe opoened', file=sys.stderr, flush=True)
            super().connection_made(transport=transport)

        def connection_lost(self, exc):
            print('pipe closed', file=sys.stderr, flush=True)
            super().connection_lost(exc)

        def data_received(self, data):
            if data == b'\x03':
                sys.exit()
            on_data_received(data)
            super().data_received(data)

    return TermReaderProtocol


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        pipe_transport = loop.connect_read_pipe(
            get_term_reader_protocol(lambda d: print(d)), sys.stdin
        )
        loop.run_until_complete(pipe_transport)
        loop.run_forever()
    finally:
        loop.close()
