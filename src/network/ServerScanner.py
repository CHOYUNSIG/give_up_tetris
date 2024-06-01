import socket
import struct
from threading import Thread, Lock
import netifaces
from time import sleep


class ServerScanner:
    class ServerScanThread(Thread):
        def __init__(self, ip: int | str, port: int, timeout: float = 0.5):
            """
            로컬 네트워크 서버 스캔 스레드
            :param ip: IP 주소
            :param port: 포트 번호
            """
            Thread.__init__(self, daemon=True)
            if type(ip) is int:
                ip = socket.inet_ntoa(struct.pack('!I', ip))
            self.ip: str = ip
            self.port = port
            self.result: tuple[str, int] | None = None
            self.timeout = timeout

        def run(self):
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(self.timeout)
                client_socket.connect((self.ip, self.port))
                self.result = (self.ip, self.port)
                client_socket.close()
            except OSError:
                pass

        def join(self, *args, **kwargs) -> tuple[str, int] | None:
            super().join(*args, **kwargs)
            return self.result

    def __init__(self):
        """
        서버 스캐너
        """
        self.__scanning = False
        self.__server_list: list[tuple[str, int]] = []
        self.__lock = Lock()

    def scan(self, port: int) -> None:
        """
        비동기적으로 스캔을 수행한다.
        """
        self.__lock.acquire()
        scanning = self.__scanning
        self.__lock.release()
        if scanning:
            return
        self.__lock.acquire()
        self.__scanning = True
        self.__lock.release()

        def scanning() -> None:
            threads: list[ServerScanner.ServerScanThread] = []
            for prefix, mask in get_iface_list():
                for i in range(2, (1 << 32) - 1 & ~mask):
                    ip = prefix + i
                    thread = self.ServerScanThread(ip, port)
                    threads.append(thread)
                    thread.start()
            server_list = list(filter(lambda x: x is not None, [thread.join() for thread in threads]))
            self.__lock.acquire()
            self.__server_list = server_list.copy()
            self.__scanning = False
            self.__lock.release()

        Thread(target=scanning, daemon=True).start()

    def get_server_list(self) -> list[tuple[str, int]]:
        """
        스캔된 서버 IP 주소 현황을 반환한다.
        :return: (IP 주소, 포트 번호) 튜플들이 담긴 튜플
        """
        sleep(0)
        self.__lock.acquire()
        server_list = self.__server_list.copy()
        self.__lock.release()
        return server_list


def get_iface_list() -> list[tuple[int, int]]:
    """
    현재 기기의 네트워크 인터페이스마다 네트워크 주소 접두사, 서브넷 마스크를 구한다.
    :return: 정수 자료형의 (주소 접두사, 서브넷 마스크)가 담긴 리스트
    """
    result = []
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        ifaddresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET not in ifaddresses:
            continue
        for addr_info in ifaddresses[netifaces.AF_INET]:
            ip_addr = addr_info['addr']
            netmask = addr_info['netmask']
            if ip_addr == '127.0.0.1':
                continue
            ip_addr_bin = struct.unpack('!I', socket.inet_aton(ip_addr))[0]
            netmask_bin = struct.unpack('!I', socket.inet_aton(netmask))[0]
            result.append((ip_addr_bin & netmask_bin, netmask_bin))
    return result


if __name__ == "__main__":
    scanner = ServerScanner()
    scanner.scan(int(input("enter the port number: ")))
    while True:
        print(scanner.get_server_list())
