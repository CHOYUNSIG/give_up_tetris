from typing import Final
from enum import auto, unique
from src.network.PairSocket import MessageType

tetris_port: Final[int] = 4321


@unique
class TetrisMessageType(MessageType):
    """
    테트리스 메시지 정의
    """
    chat = auto()  # 채팅 메시지
    chat_r = auto()
    ready = auto()  # 준비 메시지
    ready_r = auto()
    busy = auto()  # 준비 취소 메시지
    busy_r = auto()

    mdchngd = auto()  # 모드 변경
    mdchngd_r = auto()

    start = auto()  # 게임 시작
    start_r = auto()
    ended = auto()  # 게임 종료
    ended_r = auto()

    map_req = auto()  # 게임 맵 요청
    map = auto()
    score_req = auto()  # 점수 요청
    score = auto()
    queue_req = auto()  # 블록 대기 큐 요청
    queue = auto()
    pos_req = auto()  # 플레이어 블록 좌표 요청
    pos = auto()

    all_req = auto()  # 게임의 모든 데이터 요청 (experimental)
    all = auto()

    ctrlkey = auto()  # 게임 조작키
    ctrlkey_r = auto()
