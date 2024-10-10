import logging
import re
import subprocess
import time

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw

from text_rec import TextRecognizer


logger = logging.getLogger('main')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
log_format = '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s'
formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


text_recognizer = TextRecognizer()

window_title = "22041216C"


def activate_window():
    """激活窗口"""
    window = gw.getWindowsWithTitle(window_title)[0]
    window.activate()
    return window


def check_screen():
    """检查屏幕图像"""
    cmd = ["adb", "exec-out", "screencap", "-p"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    image_data = np.frombuffer(result.stdout, np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

    question_num_image = image[120:180, 445:620]  # 题号

    left_top_image = image[620:720, 280:430]    # 当前的左边数字
    right_top_image = image[620:720, 660:800]   # 当前的右边数字

    left_bot_image = image[890:970, 370:470]   # 下一个左边数字
    right_bot_image = image[890:970, 630:730]  # 下一个右边数字

    button1_image = image[1480:1600, 400:700]   # 按钮: 开心收下

    images = [
        question_num_image, 
        left_top_image, right_top_image, 
        left_bot_image, right_bot_image,
        button1_image
    ]

    texts = text_recognizer(images)

    # 计算人眼对颜色亮度敏感度的加权
    # 参考: https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/tdpf/1/1/art00005
    image = image.astype(np.float32) / 255.0
    brightness = np.mean(0.299 * image[:, :, 2] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 0])

    return texts, brightness


def is_solve_start(texts, brightness):
    """判断是否开始答题"""
    question_num_text = texts[0]

    # 1. 识别到的文本中含有"题", 例如 "1/10题"
    # 2. 画面亮度变亮，亮度大于0.5
    if question_num_text and "题" in question_num_text and brightness > 0.5:
        match = re.match(r"(\d+)/(\d+)", question_num_text)
        if match:
            total = int(match.group(2))
            return True, total
    return False, -1


def compare_numbers(left_text, right_text, flag_name):
    try:
        num1 = int(left_text)
        num2 = int(right_text)
        return num1 > num2
    except:
        return False


def draw_less_than(window):
    """画小于号"""
    pyautogui.moveTo(window.left + 300, window.top + 600, duration=0.01)
    pyautogui.mouseDown(button='left')
    pyautogui.moveTo(window.left + 200, window.top + 700, duration=0.01)
    pyautogui.moveTo(window.left + 300, window.top + 800, duration=0.01)
    pyautogui.mouseUp(button='left')


def draw_greater_than(window):
    """画大于号"""
    pyautogui.moveTo(window.left + 200, window.top + 600, duration=0.01)
    pyautogui.mouseDown(button='left')
    pyautogui.moveTo(window.left + 300, window.top + 700, duration=0.01)
    pyautogui.moveTo(window.left + 200, window.top + 800, duration=0.01)
    pyautogui.mouseUp(button='left')


def is_button(texts, brightness):
    button1_text = texts[5]
    if button1_text and "开心收下" in button1_text:
        window = gw.getWindowsWithTitle(window_title)[0]
        window.activate()

        # 点击开心收下
        logger.info(f"点击开心收下")
        pyautogui.moveTo(window.left + 220, window.top + 630, duration=0.01)
        pyautogui.mouseDown(button='left')
        pyautogui.mouseUp(button='left')

        # 点击继续
        logger.info(f"点击继续")
        pyautogui.moveTo(window.left + 330, window.top + 940, duration=0.01)
        pyautogui.mouseDown(button='left')
        pyautogui.mouseUp(button='left')

        # 点击继续pk
        logger.info(f"点击继续pk")
        pyautogui.moveTo(window.left + 230, window.top + 830, duration=0.01)
        pyautogui.mouseDown(button='left')
        pyautogui.mouseUp(button='left')

        
def main():
    window = activate_window()

    while True:
        texts, brightness = check_screen()
        is_solve, question_number = is_solve_start(texts, brightness)
        if is_solve:
            flag1 = compare_numbers(texts[1], texts[2], "当前")
            flag2 = compare_numbers(texts[3], texts[4], "下一行")

            logger.info(f"左边: {texts[1]}, 右边: {texts[2]}")
            if flag1:
                logger.info(f"画大于号")
                draw_greater_than(window)
            else:
                logger.info(f"画小于号")
                draw_less_than(window)

            # 给手机留出充分的时间反应一下
            time.sleep(0.02)

            logger.info(f"左边: {texts[3]}, 右边: {texts[4]}")
            if flag2:
                logger.info(f"画大于号")
                draw_greater_than(window)
            else:
                logger.info(f"画小于号")
                draw_less_than(window)

            time.sleep(0.2)

        is_button(texts, brightness)


if __name__ == "__main__":
    main()

