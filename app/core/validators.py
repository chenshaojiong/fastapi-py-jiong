import re
from typing import Optional, Any
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime, date
from fastapi import HTTPException

class PasswordValidator:
    """密码验证器"""
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        验证密码强度：
        - 至少8个字符
        - 至少一个大写字母
        - 至少一个小写字母
        - 至少一个数字
        - 至少一个特殊字符
        """
        if len(password) < 8:
            return False
        
        patterns = [
            r'[A-Z]',      # 大写字母
            r'[a-z]',      # 小写字母
            r'[0-9]',      # 数字
            r'[!@#$%^&*(),.?":{}|<>]'  # 特殊字符
        ]
        
        return all(re.search(pattern, password) for pattern in patterns)
    
    @staticmethod
    def get_password_requirements() -> str:
        return "密码必须至少8个字符，包含大小写字母、数字和特殊字符"

class PhoneValidator:
    """手机号验证器"""
    
    @staticmethod
    def validate_chinese_phone(phone: str) -> bool:
        """验证中国大陆手机号"""
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """格式化手机号：188-8888-8888"""
        if len(phone) == 11:
            return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
        return phone

class IDCardValidator:
    """身份证验证器"""
    
    @staticmethod
    def validate_chinese_id(id_card: str) -> bool:
        """验证中国大陆身份证（18位）"""
        if not re.match(r'^\d{17}[\dXx]$', id_card):
            return False
        
        # 验证出生日期
        try:
            birth_date = datetime.strptime(id_card[6:14], '%Y%m%d').date()
            if birth_date > date.today():
                return False
        except ValueError:
            return False
        
        # 验证校验码
        factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        checksums = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        
        total = sum(int(id_card[i]) * factors[i] for i in range(17))
        remainder = total % 11
        
        return checksums[remainder] == id_card[17].upper()
    
    @staticmethod
    def extract_birth_date(id_card: str) -> Optional[date]:
        """从身份证提取出生日期"""
        if IDCardValidator.validate_chinese_id(id_card):
            return datetime.strptime(id_card[6:14], '%Y%m%d').date()
        return None
    
    @staticmethod
    def extract_gender(id_card: str) -> Optional[str]:
        """从身份证提取性别"""
        if IDCardValidator.validate_chinese_id(id_card):
            gender_digit = int(id_card[16])
            return "男" if gender_digit % 2 == 1 else "女"
        return None

class EmailValidator:
    """邮箱验证器（扩展）"""
    
    @staticmethod
    def validate_email_domain(email: str, allowed_domains: list = None) -> bool:
        """验证邮箱域名"""
        if allowed_domains is None:
            allowed_domains = ['gmail.com', 'qq.com', '163.com', 'outlook.com']
        
        domain = email.split('@')[-1].lower()
        return domain in allowed_domains
    
    @staticmethod
    def mask_email(email: str) -> str:
        """隐藏邮箱：tes***@example.com"""
        local, domain = email.split('@')
        if len(local) > 3:
            masked_local = local[:3] + '*' * (len(local) - 3)
        else:
            masked_local = local[0] + '*' * (len(local) - 1)
        return f"{masked_local}@{domain}"

class UsernameValidator:
    """用户名验证器"""
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        验证用户名：
        - 3-20个字符
        - 只能包含字母、数字、下划线、连字符
        - 不能以下划线或连字符开头或结尾
        """
        if len(username) < 3 or len(username) > 20:
            return False
        
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', username):
            return False
        
        # 检查是否包含连续的下划线或连字符
        if re.search(r'[_-]{2,}', username):
            return False
        
        return True
    
    @staticmethod
    def get_username_requirements() -> str:
        return "用户名必须3-20个字符，只能包含字母、数字、下划线、连字符，不能以下划线或连字符开头或结尾"

class DateValidator:
    """日期验证器"""
    
    @staticmethod
    def validate_age(birth_date: date, min_age: int = 18, max_age: int = 100) -> bool:
        """验证年龄范围"""
        today = date.today()
        age = today.year - birth_date.year
        
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        return min_age <= age <= max_age
    
    @staticmethod
    def validate_future_date(target_date: date, allow_today: bool = False) -> bool:
        """验证是否是未来日期"""
        today = date.today()
        if allow_today:
            return target_date >= today
        return target_date > today

class FileValidator:
    """文件验证器"""
    
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
        """验证文件扩展名"""
        import os
        ext = os.path.splitext(filename)[1].lower()
        return ext in allowed_extensions
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int = MAX_FILE_SIZE) -> bool:
        """验证文件大小"""
        return file_size <= max_size
    
    @staticmethod
    def validate_image_file(filename: str) -> bool:
        """验证图片文件"""
        return FileValidator.validate_file_extension(filename, FileValidator.ALLOWED_IMAGE_EXTENSIONS)
    
    @staticmethod
    def validate_document_file(filename: str) -> bool:
        """验证文档文件"""
        return FileValidator.validate_file_extension(filename, FileValidator.ALLOWED_DOCUMENT_EXTENSIONS)

# 自定义Pydantic验证器装饰器
def validate_password_strength(field: str = "password"):
    """密码强度验证装饰器"""
    def decorator(cls):
        original_validator = getattr(cls, f"validate_{field}", None)
        
        @validator(field)
        def validate_password(cls, v):
            if not PasswordValidator.validate_password_strength(v):
                raiseValidateException(PasswordValidator.get_password_requirements())
            return v
        
        setattr(cls, f"_validate_{field}_strength", validate_password)
        return cls
    
    return decorator

def validate_phone_number(field: str = "phone"):
    """手机号验证装饰器"""
    def decorator(cls):
        @validator(field)
        def validate_phone(cls, v):
            if v and not PhoneValidator.validate_chinese_phone(v):
                raiseValidateException("无效的手机号码")
            return v
        return cls
    return decorator

def validate_username_format(field: str = "username"):
    """用户名格式验证装饰器"""
    def decorator(cls):
        @validator(field)
        def validate_username(cls, v):
            if not UsernameValidator.validate_username(v):
                raiseValidateException(UsernameValidator.get_username_requirements())
            return v
        return cls
    return decorator

   
def raiseValidateException( msg: str):
    """抛出验证异常"""
    raise HTTPException(
                status_code=400,
                detail=msg
            )