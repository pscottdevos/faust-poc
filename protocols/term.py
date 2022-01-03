import asyncio
import atexit
import sys
import termios as tm


# Indexes for termios list.
IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

def setraw(fd, when=tm.TCSAFLUSH):
    """Put terminal into a raw mode."""
    mode = tm.tcgetattr(fd)
    mode[IFLAG] = mode[IFLAG] & ~(tm.BRKINT | tm.ICRNL | tm.INPCK | tm.ISTRIP | tm.IXON)
    #mode[OFLAG] = mode[OFLAG] & ~(tm.OPOST)
    mode[CFLAG] = mode[CFLAG] & ~(tm.CSIZE | tm.PARENB)
    mode[CFLAG] = mode[CFLAG] | tm.CS8
    mode[LFLAG] = mode[LFLAG] & ~(tm.ECHO | tm.ICANON | tm.IEXTEN | tm.ISIG)
    mode[CC][tm.VMIN] = 1
    mode[CC][tm.VTIME] = 0
    tm.tcsetattr(fd, when, mode)


def get_term_reader_protocol(on_data_received=lambda d: d, set_echo_enabled=False):

    class TermReaderProtocol(asyncio.Protocol):
        
        def __init__(self, *args, **kwargs):
            self.configure(set_echo_enabled)
            super().__init__(*args, **kwargs)

        @staticmethod
        def configure(set_echo_enabled=False):
            fd = sys.stdin.fileno()
            default_mode = tm.tcgetattr(fd)
            atexit.register(tm.tcsetattr, fd, tm.TCSADRAIN, default_mode)
            mode = tm.tcgetattr(fd)
            if set_echo_enabled:
                mode[LFLAG] |= tm.ECHO
            else:
                mode[LFLAG] &= ~tm.ECHO
            setraw(fd)

        def connection_made(self, transport):
            print('pipe opoened', file=sys.stderr, flush=True)
            super().connection_made(transport=transport)

        def connection_lost(self, exc):
            print('pipe closed', file=sys.stderr, flush=True)
            super().connection_lost(exc)

        def data_received(self, data):
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
