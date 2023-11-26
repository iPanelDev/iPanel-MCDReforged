import json


class Packet:
    '''数据包'''

    def __init__(self, text: str) -> None:
        self.__obj___: dict = json.loads(text)
        self.type: str = self.__obj___.get('type')
        self.sub_type: str = self.__obj___.get('subType')
        self.data: dict | str = self.__obj___.get('data')
        self.time: int = self.__obj___.get('time')
