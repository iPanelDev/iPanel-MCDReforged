import json


class Packet:
    '''数据包'''

    class Sender:
        '''发送者'''

        def __init__(self, obj: dict) -> None:
            self.type: str = obj.get('type')
            self.address: str = obj.get('address')
            self.name: str = obj.get('name')

    def __init__(self, text: str) -> None:
        self.__obj___: dict = json.loads(text)
        self.type: str = self.__obj___.get('type')
        self.sub_type: str = self.__obj___.get('sub_type')
        self.data: dict | str = self.__obj___.get('data')
        self.sender = self.Sender(self.__obj___.get('sender'))
        self.time: int = self.__obj___.get('time')
