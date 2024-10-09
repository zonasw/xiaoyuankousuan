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
logger.addHandler(console_handler)

text_recognizer = TextRecognizer()

window_title = "22041216C"


def check_screen():
    """检查屏幕图像"""
    cmd = ["adb", "exec-out", "screencap", "-p"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    image_data = np.frombuffer(result.stdout, np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    return image


def is_solve_start(image):
    question_num_image = image[120:180, 445:620]
    texts = text_recognizer([question_num_image])
    if texts and "题" in texts[0]:
        text = texts[0]
        match = re.match(r"(\d+)/(\d+)", text)
        total = int(match.group(2))
        return True, total
    return False, -1
          

def current_flag(image):
    left_top_image = image[575:780, 200:440]
    right_top_image = image[575:780, 645:880]
    numbers = text_recognizer([left_top_image, right_top_image])
    try:
        numbers = [int(x) for x in numbers]
        logger.info(f"当前左边的数字为: {numbers[0]}, 右边的数字为: {numbers[1]}")
        return numbers[0] > numbers[1]
    except:
        return False


def next_flag(image):
    left_bot_image = image[865:1000, 200:480]
    right_top_image = image[865:1000, 615:880]
    numbers = text_recognizer([left_bot_image, right_top_image])
    try:
        numbers = [int(x) for x in numbers]
        logger.info(f"下一行左边数字为: {numbers[0]}, 右边的数字为: {numbers[1]}")
        return numbers[0] > numbers[1]
    except:
        return False


def draw_less_than():
    """画小于号"""
    window = gw.getWindowsWithTitle(window_title)[0]
    window.activate()

    pyautogui.moveTo(window.left + 300, window.top + 600, duration=0.01)
    pyautogui.mouseDown(button='left')
    pyautogui.moveTo(window.left + 200, window.top + 700, duration=0.15)
    pyautogui.moveTo(window.left + 300, window.top + 800, duration=0.15)
    pyautogui.mouseUp(button='left')


def draw_greater_than():
    """画大于号"""
    window = gw.getWindowsWithTitle(window_title)[0]
    window.activate()

    pyautogui.moveTo(window.left + 200, window.top + 600, duration=0.01)
    pyautogui.mouseDown(button='left')
    pyautogui.moveTo(window.left + 300, window.top + 700, duration=0.15)
    pyautogui.moveTo(window.left + 200, window.top + 800, duration=0.15)
    pyautogui.mouseUp(button='left')


def is_button(image):
    sub_image = image[1480:1600, 400:700]
    texts = text_recognizer([sub_image])

    if texts and texts[0] and "开心收下" in texts[0]:
        window = gw.getWindowsWithTitle(window_title)[0]
        window.activate()
        # 点击开心收下
        pyautogui.moveTo(window.left + 220, window.top + 630, duration=0.01)
        pyautogui.mouseDown(button='left')
        pyautogui.mouseUp(button='left')

        # 点击继续
        pyautogui.moveTo(window.left + 330, window.top + 940, duration=0.01)
        pyautogui.mouseDown(button='left')
        pyautogui.mouseUp(button='left')

        # 点击继续pk
        pyautogui.moveTo(window.left + 230, window.top + 830, duration=0.01)
        pyautogui.mouseDown(button='left')
        pyautogui.mouseUp(button='left')

        
def main():
    while True:
        image = check_screen()
        is_solve, question_number = is_solve_start(image)

        while is_solve:
            flag = current_flag(image)
            if flag:
                draw_greater_than()
            else:
                draw_less_than()
            time.sleep(0.3)

            image = check_screen()
            is_solve, question_number = is_solve_start(image)

        is_button(image)


if __name__ == "__main__":
    main()

