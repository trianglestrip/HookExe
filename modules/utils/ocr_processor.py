"""
OCR处理器模块
功能：封装OCR识别、可视化标记和保存功能的统一处理器
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from typing import List, Dict, Optional, Union
from ..core import OCREngine


class OCRProcessor:
    """OCR处理器类，提供统一的OCR识别、绘制和保存功能"""
    
    def __init__(self, 
                 ocr_engine: Optional[OCREngine] = None, 
                 logger=None,
                 save_path: str = "./screenshots"):
        """
        初始化OCR处理器
        
        Args:
            ocr_engine: OCR引擎实例，如果为None则会自动创建
            logger: 日志记录器实例
            save_path: 截图保存路径
        """
        self.ocr_engine = ocr_engine
        self.logger = logger
        self.save_path = save_path
        
        # 如果没有提供OCR引擎，创建默认实例
        if self.ocr_engine is None:
            self._init_default_ocr_engine()
    
    def _init_default_ocr_engine(self):
        """初始化默认OCR引擎"""
        try:
            self.log_message("正在初始化OCR引擎...")
            self.ocr_engine = OCREngine(
                lang="ch",
                use_gpu=False,
                confidence_threshold=0.7  # 使用项目标准配置
            )
            self.log_message("OCR引擎初始化完成（标准模式，平均识别时间~0.2秒）")
        except Exception as e:
            self.log_message(f"OCR引擎初始化失败: {e}", "ERROR")
            self.ocr_engine = None
    
    def log_message(self, message: str, level: str = "INFO"):
        """记录日志消息"""
        if self.logger:
            self.logger.log_message(message, level)
        else:
            print(f"[{level}] {message}")
    
    def recognize_and_save(self, 
                          screenshot: Image.Image, 
                          process_info: Optional[Dict] = None,
                          filename_prefix: str = "capture") -> List[Dict]:
        """
        OCR文字识别并保存结果（统一封装的核心功能）
        
        Args:
            screenshot: 截图 PIL 图像对象
            process_info: 进程信息字典，包含name和pid等信息（可选）
            filename_prefix: 文件名前缀，默认为"capture"
            
        Returns:
            OCR识别结果列表
        """
        if self.ocr_engine is None:
            self.log_message("OCR引擎未初始化，无法进行识别", "ERROR")
            # 保存原始截图
            self.save_screenshot(screenshot, [], process_info, filename_prefix)
            return []
        
        try:
            # 使用OCR引擎识别PIL图像
            high_confidence_results = self.ocr_engine.recognize_pil_image(screenshot)
            
            if high_confidence_results:
                self.log_message(f"找到 {len(high_confidence_results)} 个高置信度结果")
                
                # 在截图上绘制OCR结果
                enhanced_screenshot = self.draw_ocr_results(screenshot, high_confidence_results)
                
                # 保存结果
                self.save_screenshot(enhanced_screenshot, high_confidence_results, process_info, filename_prefix)
                
                return high_confidence_results
            else:
                self.log_message("没有找到置信度大于0.7的识别结果")
                
                # 即使没有OCR结果，也保存原始截图
                self.save_screenshot(screenshot, [], process_info, filename_prefix)
                
                return []
                
        except Exception as e:
            self.log_message(f"OCR识别出错: {e}", "ERROR")
            
            # 发生错误时，保存原始截图
            self.save_screenshot(screenshot, [], process_info, filename_prefix)
            
            return []
    
    def draw_ocr_results(self, image: Image.Image, ocr_results: List[Dict]) -> Image.Image:
        """
        在图像上绘制OCR识别结果（统一的可视化标记功能）
        
        Args:
            image: PIL图像对象
            ocr_results: OCR识别结果列表
            
        Returns:
            绘制后的PIL图像对象
        """
        try:
            # 创建可编辑的图像副本
            draw_image = image.copy()
            draw = ImageDraw.Draw(draw_image)
            
            # 尝试加载中文字体
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 16)
                font_small = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 12)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                    font_small = ImageFont.truetype("arial.ttf", 12)
                except:
                    font = ImageFont.load_default()
                    font_small = ImageFont.load_default()
            
            self.log_message(f"开始绘制 {len(ocr_results)} 个高置信度文字框")
            
            for i, result in enumerate(ocr_results, 1):
                box = result['box']
                text = result['text']
                confidence = result['confidence']
                
                # 转换坐标点
                points = np.array(box, dtype=np.int32)
                
                # 绘制红色边框
                draw.polygon([tuple(p) for p in points], outline='red', width=2)
                
                # 在文本框上方显示置信度
                x_min = min([p[0] for p in points])
                y_min = min([p[1] for p in points])
                
                # 置信度文本
                conf_text = f"{confidence:.3f}"
                
                # 绘制置信度背景和文本
                try:
                    bbox = draw.textbbox((x_min, y_min - 25), conf_text, font=font_small)
                    draw.rectangle(bbox, fill='red', outline='red')
                    draw.text((x_min, y_min - 25), conf_text, fill='white', font=font_small)
                except:
                    draw.text((x_min, y_min - 25), conf_text, fill='red', font=font_small)
                
                # 在文本框左下方显示识别文本（限制20字符内）
                if len(text) <= 20:
                    y_max = max([p[1] for p in points])
                    try:
                        text_bbox = draw.textbbox((x_min, y_max + 5), text, font=font_small)
                        draw.rectangle(text_bbox, fill='blue', outline='blue')
                        draw.text((x_min, y_max + 5), text, fill='white', font=font_small)
                    except:
                        draw.text((x_min, y_max + 5), text, fill='blue', font=font_small)
            
            self.log_message("文字框绘制完成")
            return draw_image
            
        except Exception as e:
            self.log_message(f"绘制OCR结果时出错: {e}", "ERROR")
            return image
    
    def save_screenshot(self, 
                       screenshot: Image.Image, 
                       ocr_results: List[Dict],
                       process_info: Optional[Dict] = None,
                       filename_prefix: str = "capture") -> bool:
        """
        保存截图文件（统一的智能文件命名规范）
        
        Args:
            screenshot: 截图图像（PIL格式）
            ocr_results: OCR识别结果列表
            process_info: 进程信息字典，包含name和pid等信息（可选）
            filename_prefix: 文件名前缀
            
        Returns:
            是否保存成功
        """
        try:
            # 确保保存路径存在
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path, exist_ok=True)
            
            # 生成文件名（遵循项目智能命名规范）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if process_info and 'name' in process_info and 'pid' in process_info:
                # 包含进程信息的命名：进程名_PID_时间戳_OCR_N个文字.png
                if self.ocr_engine and len(ocr_results) > 0:
                    filename = f"{process_info['name']}_{process_info['pid']}_{timestamp}_OCR_{len(ocr_results)}个文字.png"
                else:
                    filename = f"{process_info['name']}_{process_info['pid']}_{timestamp}_无OCR.png"
            else:
                # 通用命名：前缀_时间戳_OCR_N个文字.png
                if self.ocr_engine and len(ocr_results) > 0:
                    filename = f"{filename_prefix}_{timestamp}_OCR_{len(ocr_results)}个文字.png"
                else:
                    filename = f"{filename_prefix}_{timestamp}_无OCR.png"
            
            file_path = os.path.join(self.save_path, filename)
            
            # 保存截图
            screenshot.save(file_path)
            
            self.log_message(f"截图完成，已保存到: {file_path}")
            self.log_message(f"OCR结果: {len(ocr_results)} 个高置信度文字")
            
            # 输出OCR识别结果详情
            if ocr_results:
                self.log_message("\n=== OCR识别结果 ===")
                for i, result in enumerate(ocr_results, 1):
                    self.log_message(f"{i}. 文本: {result['text']}, 置信度: {result['confidence']:.3f}")
                self.log_message("=" * 30)
            
            return True
            
        except Exception as e:
            self.log_message(f"保存截图失败: {e}", "ERROR")
            return False
    
    def set_save_path(self, save_path: str):
        """设置保存路径"""
        self.save_path = save_path
    
    def get_save_path(self) -> str:
        """获取保存路径"""
        return self.save_path


# 便捷函数
def create_ocr_processor(ocr_engine: Optional[OCREngine] = None, 
                        logger=None,
                        save_path: str = "./screenshots") -> OCRProcessor:
    """
    创建OCR处理器实例的便捷函数
    
    Args:
        ocr_engine: OCR引擎实例，如果为None则会自动创建
        logger: 日志记录器实例
        save_path: 截图保存路径
        
    Returns:
        OCRProcessor实例
    """
    return OCRProcessor(ocr_engine, logger, save_path)