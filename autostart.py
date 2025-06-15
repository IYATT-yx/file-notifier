"""自启动设置"""
import constants as const

import winreg
from tkinter import messagebox as mb

class AutoStart:
    @staticmethod
    def setAutoStart() -> tuple[bool, Exception | None]:
        """设置开机自启动
        
        Returns:
            tuple[bool, Exception | None]: (是否设置成功, 错误信息)
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                const.AutoStart.autoStartRegPath,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, const.Info.projectName, 0, winreg.REG_SZ, const.AutoStart.commandStr)
            winreg.CloseKey(key)
            return True, None
        except Exception as e:
            return False, e

    @staticmethod
    def unsetAutoStart() -> tuple[bool, Exception | None | str]:
        """取消开机自启动

        Returns:
            tuple[bool, Exception | None]: (是否取消成功, 错误信息)
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                const.AutoStart.autoStartRegPath,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, const.Info.projectName)
            winreg.CloseKey(key)
            return True, None
        except FileNotFoundError:
            return True, '未设置自启动，无需取消'
        except Exception as e:
            return False, e

    @staticmethod
    def checkAutoStart() -> tuple[bool, Exception | None]:
        """检查是否设置开机自启动

        Returns:
            tuple[bool, Exception | None]: (是否设置自启动, 错误信息)
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                const.AutoStart.autoStartRegPath,
                0,
                winreg.KEY_READ
            )
            winreg.QueryValueEx(key, const.Info.projectName)
            winreg.CloseKey(key)
            return True, None
        except FileNotFoundError:
            return False, None
        except Exception as e:
            return False, e
            

