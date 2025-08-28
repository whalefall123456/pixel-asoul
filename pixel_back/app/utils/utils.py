"""
@Author: star_482
@Date: 2025/8/26 
@File: utils 
@Description:
"""

from typing import List
from PIL import Image
import numpy as np


def color_array_to_png(color_array: List[str], width: int, height: int, output_path: str = None) -> bytes:
    """
    将颜色数组转换为PNG图片格式
    
    Args:
        color_array: 颜色数组，每个元素为十六进制颜色码（如"#FF0000"）
        width: 图片宽度
        height: 图片高度
        output_path: 可选，输出文件路径，如果提供则保存到文件
        
    Returns:
        bytes: PNG图片的字节数据
        
    Raises:
        ValueError: 当颜色数组长度与指定的宽高不匹配时
    """
    # 验证输入参数
    if len(color_array) != width * height:
        raise ValueError(f"颜色数组长度({len(color_array)})与指定尺寸({width}x{height}={width*height})不匹配")
    
    # 创建一个numpy数组来存储RGB值
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 将十六进制颜色转换为RGB值并填充到数组中
    for i, color_hex in enumerate(color_array):
        # 解析十六进制颜色码
        if color_hex.startswith('#'):
            color_hex = color_hex[1:]
        
        # 将十六进制转换为RGB
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        
        # 计算在数组中的位置
        y = i // width
        x = i % width
        
        # 填充RGB值
        img_array[y, x] = [r, g, b]
    
    # 创建PIL图像
    img = Image.fromarray(img_array, 'RGB')
    
    # 如果指定了输出路径，则保存到文件
    if output_path:
        img.save(output_path, 'PNG')
    
    # 将图像转换为字节数据
    from io import BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


def png_to_color_array(png_path: str = None, png_bytes: bytes = None) -> List[str]:
    """
    将PNG图像转换为十六进制颜色值数组
    
    Args:
        png_path: PNG图片文件路径
        png_bytes: PNG图片字节数据
        
    Returns:
        List[str]: 颜色数组，每个元素为十六进制颜色码（如"#FF0000"）
        
    Raises:
        ValueError: 当既没有提供文件路径也没有提供字节数据时
    """
    # 验证输入参数
    if not png_path and not png_bytes:
        raise ValueError("必须提供png_path或png_bytes参数")
    
    # 加载图像
    if png_path:
        img = Image.open(png_path)
    else:
        from io import BytesIO
        img = Image.open(BytesIO(png_bytes))
    
    # 转换为RGB模式（以防是RGBA或其他模式）
    img = img.convert('RGB')
    
    # 转换为numpy数组
    img_array = np.array(img)
    
    # 获取图像尺寸
    height, width = img_array.shape[:2]
    
    # 创建颜色数组
    color_array = []
    
    # 遍历每个像素
    for y in range(height):
        for x in range(width):
            # 获取RGB值
            r, g, b = img_array[y, x]
            
            # 转换为十六进制颜色码
            color_hex = f"#{r:02X}{g:02X}{b:02X}"
            
            # 添加到数组
            color_array.append(color_hex)
    
    return color_array