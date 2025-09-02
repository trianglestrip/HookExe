"""
OCR引擎封装模块
提供统一的OCR识别接口，支持图像文件和像素数组识别
"""

import numpy as np
from PIL import Image
import cv2  # type: ignore
from paddleocr import PaddleOCR
from typing import List, Dict, Optional, Union, Tuple
import os

class OCREngine:
    """OCR识别引擎类"""
    
    def __init__(self, 
                 lang: str = "ch",
                 use_gpu: bool = False,
                 confidence_threshold: float = 0.8):
        """
        初始化OCR引擎
        
        Args:
            lang: 语言模式，默认中文 "ch"
            use_gpu: 是否使用GPU，默认False
            confidence_threshold: 置信度阈值，默认0.8
        """
        self.lang = lang
        self.use_gpu = use_gpu
        self.confidence_threshold = confidence_threshold
        self.ocr = None
        
        print("正在初始化OCR模型...")
        self._init_ocr()
    
    def _init_ocr(self):
        """初始化PaddleOCR模型"""
        try:
            device = "gpu" if self.use_gpu else "cpu"
            self.ocr = PaddleOCR(
                use_doc_orientation_classify=False,  # 不使用文档方向分类模型
                use_doc_unwarping=False,  # 不使用文本图像矫正模型
                use_textline_orientation=False,  # 不使用文本行方向分类模型
                text_detection_model_name="PP-OCRv5_mobile__det",
                text_recognition_model_name="PP-OCRv5_mobile_rec",
                lang=self.lang,
                device=device,
                show_log=False  # 不显示详细日志
            )
            print(f"OCR模型初始化完成 (语言: {self.lang}, 设备: {device})")
        except Exception as e:
            print(f"OCR模型初始化失败: {e}")
            self.ocr = None
    
    def recognize_image_file(self, image_path: str) -> List[Dict]:
        """
        识别图像文件中的文字
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            识别结果列表，每个元素包含text, confidence, box信息
        """
        if not os.path.exists(image_path):
            print(f"图像文件不存在: {image_path}")
            return []
        
        if self.ocr is None:
            print("OCR模型未初始化，无法进行识别")
            return []
        
        try:
            print(f"正在识别图像文件: {image_path}")
            result = self.ocr.ocr(image_path, cls=False)  # type: ignore
            return self._parse_ocr_result(result)
        except Exception as e:
            print(f"识别图像文件时出错: {e}")
            return []
    
    def recognize_image_array(self, img_array: np.ndarray) -> List[Dict]:
        """
        识别像素数组中的文字
        
        Args:
            img_array: 图像像素数组 (numpy.ndarray)
            
        Returns:
            识别结果列表，每个元素包含text, confidence, box信息
        """
        if self.ocr is None:
            print("OCR模型未初始化，无法进行识别")
            return []
        
        try:
            print(f"正在识别图像数组，尺寸: {img_array.shape}")
            result = self.ocr.ocr(img_array, cls=False)  # type: ignore
            return self._parse_ocr_result(result)
        except Exception as e:
            print(f"识别图像数组时出错: {e}")
            return []
    
    def recognize_pil_image(self, pil_image: Image.Image) -> List[Dict]:
        """
        识别PIL图像中的文字
        
        Args:
            pil_image: PIL Image对象
            
        Returns:
            识别结果列表，每个元素包含text, confidence, box信息
        """
        # 转换PIL图像为numpy数组
        img_array = np.array(pil_image)
        return self.recognize_image_array(img_array)
    
    def _parse_ocr_result(self, result) -> List[Dict]:
        """
        解析OCR识别结果
        
        Args:
            result: PaddleOCR原始识别结果
            
        Returns:
            格式化的识别结果列表
        """
        if not result or not result[0]:
            print("未识别到任何文字")
            return []
        
        parsed_results = []
        high_confidence_results = []
        
       # print("\n=== OCR识别结果 ===")
        for line in result[0]:
            try:
                # line格式: [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, confidence)]
                box = line[0]
                text = line[1][0]
                confidence = line[1][1]
                
               # print(f"文本: {text}, 置信度: {confidence:.3f}")
                
                result_item = {
                    'text': text,
                    'confidence': confidence,
                    'box': box
                }
                parsed_results.append(result_item)
                
                # 筛选高置信度结果
                if confidence > self.confidence_threshold:
                    high_confidence_results.append(result_item)
                    
            except (IndexError, KeyError) as e:
                print(f"解析识别结果时出错: {e}")
                continue
        
        # print(f"\n=== 高置信度结果 (>{self.confidence_threshold}) ===")
        # if high_confidence_results:
        #     for i, item in enumerate(high_confidence_results, 1):
        #         print(f"{i}. 文本: {item['text']}, 置信度: {item['confidence']:.3f}")
        # else:
        #     print(f"没有找到置信度大于{self.confidence_threshold}的识别结果")
        
        return high_confidence_results
    
    def get_all_results(self, img_input: Union[str, np.ndarray, Image.Image]) -> Tuple[List[Dict], List[Dict]]:
        """
        获取所有识别结果和高置信度结果
        
        Args:
            img_input: 图像输入，可以是文件路径、numpy数组或PIL图像
            
        Returns:
            (所有结果, 高置信度结果) 的元组
        """
        if isinstance(img_input, str):
            # 文件路径
            all_results = self._recognize_and_get_all(img_input, 'file')
        elif isinstance(img_input, np.ndarray):
            # numpy数组
            all_results = self._recognize_and_get_all(img_input, 'array')
        elif isinstance(img_input, Image.Image):
            # PIL图像
            all_results = self._recognize_and_get_all(img_input, 'pil')
        else:
            print(f"不支持的图像输入类型: {type(img_input)}")
            return [], []
        
        high_confidence_results = [
            item for item in all_results 
            if item['confidence'] > self.confidence_threshold
        ]
        
        return all_results, high_confidence_results
    
    def _recognize_and_get_all(self, img_input, input_type: str) -> List[Dict]:
        """内部方法：识别并获取所有结果"""
        if self.ocr is None:
            return []
        
        try:
            if input_type == 'file':
                result = self.ocr.ocr(img_input, cls=False)  # type: ignore
            elif input_type == 'array':
                result = self.ocr.ocr(img_input, cls=False)  # type: ignore
            elif input_type == 'pil':
                img_array = np.array(img_input)
                result = self.ocr.ocr(img_array, cls=False)  # type: ignore
            else:
                return []
            
            if not result or not result[0]:
                return []
            
            all_results = []
            for line in result[0]:
                try:
                    box = line[0]
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    all_results.append({
                        'text': text,
                        'confidence': confidence,
                        'box': box
                    })
                except (IndexError, KeyError):
                    continue
            
            return all_results
            
        except Exception as e:
            print(f"识别过程中出错: {e}")
            return []
    
    def set_confidence_threshold(self, threshold: float):
        """设置置信度阈值"""
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            print(f"置信度阈值已设置为: {threshold}")
        else:
            print("置信度阈值必须在0.0-1.0之间")
    
    def get_confidence_threshold(self) -> float:
        """获取当前置信度阈值"""
        return self.confidence_threshold

# 创建默认OCR引擎实例
default_ocr_engine = None

def get_default_ocr_engine() -> OCREngine:
    """获取默认OCR引擎实例（单例模式）"""
    global default_ocr_engine
    if default_ocr_engine is None:
        default_ocr_engine = OCREngine()
    return default_ocr_engine

def recognize_image(img_input: Union[str, np.ndarray, Image.Image], 
                   confidence_threshold: float = 0.8) -> List[Dict]:
    """
    便捷函数：识别图像并返回高置信度结果
    
    Args:
        img_input: 图像输入（文件路径、numpy数组或PIL图像）
        confidence_threshold: 置信度阈值
        
    Returns:
        高置信度识别结果列表
    """
    engine = get_default_ocr_engine()
    engine.set_confidence_threshold(confidence_threshold)
    
    if isinstance(img_input, str):
        return engine.recognize_image_file(img_input)
    elif isinstance(img_input, np.ndarray):
        return engine.recognize_image_array(img_input)
    elif isinstance(img_input, Image.Image):
        return engine.recognize_pil_image(img_input)
    else:
        print(f"不支持的图像输入类型: {type(img_input)}")
        return []

# 导出主要接口
__all__ = [
    'OCREngine',
    'get_default_ocr_engine', 
    'recognize_image'
]