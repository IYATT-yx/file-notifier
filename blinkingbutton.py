"""闪烁按钮"""
import tkinter as tk

class BlinkingButton(tk.Button):
    def __init__(self, master=None, blinkColor="red", blinkInterval=500, **kwargs):
        """
        闪烁按钮

        Args:
            master: 父组件
            blinkColor: 闪烁颜色
            blinkInterval: 闪烁周期（毫秒）
            kwargs: 其它Button属性
        """
        super().__init__(master, **kwargs)
        self.master = master
        self.blinkColor = blinkColor
        self.blinkInterval = blinkInterval
        self.normalBg = self["bg"] if "bg" in kwargs else self.cget("bg")
        self.blinking = False
        self.blinkState = False

    def startBlinking(self):
        if not self.blinking:
            self.blinking = True
            self.blink()

    def stopBlinking(self):
        self.blinking = False
        self.configure(bg=self.normalBg)

    def blink(self):
        if not self.blinking:
            return

        new_color = self.blinkColor if not self.blinkState else self.normalBg
        self.configure(bg=new_color)
        self.blinkState = not self.blinkState
        self.after(self.blinkInterval, self.blink)
