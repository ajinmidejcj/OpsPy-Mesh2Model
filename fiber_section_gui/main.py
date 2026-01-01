#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication

# 添加当前目录到Python路径，以便正确导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

from gui.main_window import MainWindow

# 设置matplotlib支持中文
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
