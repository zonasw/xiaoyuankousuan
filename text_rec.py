import os
import os.path as osp
import math

import cv2
import onnxruntime
import numpy as np


class TextRecognizer:
    def __init__(
            self,
            model_path: str = "checkpoints/ch_PP-OCRv4_rec_infer.onnx",
            use_gpu: bool = False,
            word_dict_path: str = "checkpoints/rec_word_dict.txt",
    ):
        """
        初始化

        params:
            model_path (str): ONNX模型路径
            use_gpu (bool): 是否使用GPU推理
            word_dict_path (str): 字典文件路径，用于字符映射
        """
        so = onnxruntime.SessionOptions()
        so.log_severity_level = 3

        providers = ['CUDAExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        self.session = onnxruntime.InferenceSession(model_path, so, providers=providers)
        self.word_dict_path = word_dict_path

        self.rec_image_shape = [3, 48, 320]
        self.alphabet = self.load_alphabet()


    def load_alphabet(self) -> list:
        """
        加载字符字典

        return:
            list: 字符映射列表
        """
        with open(self.word_dict_path, "r", encoding="utf8") as f:
            lines = f.readlines()
        alphabet = []
        for line in lines:
            decoded_line = line.strip("\n").strip("\r\n")
            alphabet.append(decoded_line)
        alphabet.append(' ')
        return alphabet


    def decode(self, t: np.ndarray, length: int, raw: bool = False) -> str:
        """
        解码模型预测的字符索引为实际字符

        params:
            t (np.ndarray): 模型预测的字符索引
            length (int): 有效字符的长度
            raw (bool): 是否直接解码所有字符，忽略重复字符

        return:
            str: 解码后的文本
        """
        t = t[:length]
        if raw:
            return ''.join([self.alphabet[i - 1] for i in t])
        else:
            char_list = []
            for i in range(length):
                if t[i] != 0 and (not (i > 0 and t[i - 1] == t[i])):
                    char_list.append(self.alphabet[t[i] - 1])
            return ''.join(char_list)


    def resize_norm_img(self, img: np.ndarray) -> np.ndarray:
        """
        调整图像大小并归一化

        params:
            img (np.ndarray): 输入图像

        return:
            np.ndarray: 调整大小并归一化后的图像
        """
        imgC, imgH, imgW = self.rec_image_shape

        h, w = img.shape[:2]
        ratio = w / float(h)
        if math.ceil(imgH * ratio) > imgW:
            resized_w = imgW
        else:
            resized_w = int(math.ceil(imgH * ratio))

        resized_image = cv2.resize(img, (resized_w, imgH))
        resized_image = resized_image.astype('float32')
        resized_image = resized_image.transpose((2, 0, 1)) / 255
        resized_image -= 0.5
        resized_image /= 0.5
        padding_im = np.zeros((imgC, imgH, imgW), dtype=np.float32)
        padding_im[:, :, 0:resized_w] = resized_image
        return padding_im


    def __call__(self, images: list) -> list:
        """
        处理输入图像列表，返回每张图像的识别文本

        params:
            images (list of np.ndarray): 需要处理的图像列表

        return:
            list: 每张图像对应的识别文本列表
        """
        batch_images = np.array([self.resize_norm_img(im) for im in images])
        ort_inputs = {i.name: batch_images for i in self.session.get_inputs()}

        ort_outputs = self.session.run(None, ort_inputs)

        batch_preds = ort_outputs[0]
        texts = []
        for pred in batch_preds:
            length = pred.shape[0]
            pred = pred.reshape(length, -1)
            pred = np.argmax(pred, axis=1)
            sim_pred = self.decode(pred, length, raw=False)
            texts.append(sim_pred)
        return texts

