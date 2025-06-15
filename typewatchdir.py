"""WatchDir 数据结构"""

class WatchDir:
    def __init__(self, id: int, dir: str, status: int = 0):
        """监控目录对象

        Args:
            id (int): 目录ID
            dir (str): 目录路径
            status (int): 状态，0表示未监控，1表示正在监控
        """
        self.id = int(id)
        self.dir = dir
        self.status = int(status)

class BoolStr:
    @staticmethod
    def chinese2int(chineseBool: str) -> int:
        """将中文布尔值转换为整数

        Args:
            chineseBool (str): 中文布尔值，'是'或'否'

        Returns:
            int: 1表示True，0表示False
        """
        if chineseBool == '是':
            return 1
        elif chineseBool == '否':
            return 0
        else:
            raise ValueError("中文布尔值必须是'是'或'否'")
        
    @staticmethod
    def int2chinese(intBool: int) -> str:
        """将整数布尔值转换为中文

        Args:
            intBool (int): 整数布尔值，1表示True，0表示False

        Returns:
            str: '是'表示True，'否'表示False
        """
        if intBool == 1:
            return '是'
        elif intBool == 0:
            return '否'
        else:
            raise ValueError("整数布尔值必须是1或0")