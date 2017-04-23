import socket


PORT_RANGE = list(range(5001, 5100))


def find_unused_port(default=5001):
    """
    Returns first free port in range :data:`PORT_RANGE`

    :param int default:
    :rtype: int
    """
    to_select = [default] + PORT_RANGE
    for port in to_select:
        if not is_port_in_use(port):
            return port

    raise Exception("Could not find an unused port")


def is_port_in_use(port, host='127.0.0.1'):
    """
    :rtype bool:
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    return result == 0
