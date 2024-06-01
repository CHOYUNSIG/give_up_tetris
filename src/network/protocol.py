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

    game_start = auto()  # 게임 시작
    game_ended = auto()  # 게임 종료

    tetris_map_request = auto()  # 게임 맵 요청
    tetris_map = auto()  # 게임 맵
    score_request = auto()  # 점수 요청
    score = auto()  # 점수
    queue_request = auto()  # 블록 대기 큐 요청
    queue = auto()  # 블록 대기 큐
    player_pos_request = auto()  # 플레이어 블록 좌표 요청
    player_pos = auto()  # 플레이어 블록 좌표

    control_key = auto()  # 게임 조작키
