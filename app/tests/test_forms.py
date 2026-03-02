import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.validators import (
    PasswordValidator, PhoneValidator, 
    UsernameValidator, EmailValidator,
    IDCardValidator
)

client = TestClient(app)

def test_password_validator():
    """测试密码验证器"""
    # 有效密码
    assert PasswordValidator.validate_password_strength("Test@1234") == True
    assert PasswordValidator.validate_password_strength("Abcdefg1!") == True
    
    # 无效密码
    assert PasswordValidator.validate_password_strength("12345678") == False  # 无字母和特殊字符
    assert PasswordValidator.validate_password_strength("abcdefgh") == False  # 无数字和特殊字符
    assert PasswordValidator.validate_password_strength("ABCDEFGH") == False  # 无数字和特殊字符
    assert PasswordValidator.validate_password_strength("Test1234") == False   # 无特殊字符
    assert PasswordValidator.validate_password_strength("Test@123") == False   # 长度不足

def test_phone_validator():
    """测试手机号验证器"""
    # 有效手机号
    assert PhoneValidator.validate_chinese_phone("13800138000") == True
    assert PhoneValidator.validate_chinese_phone("19912345678") == True
    
    # 无效手机号
    assert PhoneValidator.validate_chinese_phone("12345678901") == False  # 无效号段
    assert PhoneValidator.validate_chinese_phone("1380013800") == False   # 长度不足
    assert PhoneValidator.validate_chinese_phone("138001380000") == False  # 长度过长
    assert PhoneValidator.validate_chinese_phone("1380013800a") == False   # 包含字母
    
    # 格式化测试
    assert PhoneValidator.format_phone("13800138000") == "138-0013-8000"

def test_username_validator():
    """测试用户名验证器"""
    # 有效用户名
    assert UsernameValidator.validate_username("testuser") == True
    assert UsernameValidator.validate_username("test-user") == True
    assert UsernameValidator.validate_username("test_user") == True
    assert UsernameValidator.validate_username("test123") == True
    
    # 无效用户名
    assert UsernameValidator.validate_username("te") == False  # 长度不足
    assert UsernameValidator.validate_username("testuser12345678901") == False  # 长度过长
    assert UsernameValidator.validate_username("_testuser") == False  # 下划线开头
    assert UsernameValidator.validate_username("testuser_") == False  # 下划线结尾
    assert UsernameValidator.validate_username("test--user") == False  # 连续连字符
    assert UsernameValidator.validate_username("test@@user") == False  # 非法字符

def test_id_card_validator():
    """测试身份证验证器"""
    # 有效身份证（示例，非真实）
    assert IDCardValidator.validate_chinese_id("11010119900307663X") == True
    
    # 无效身份证
    assert IDCardValidator.validate_chinese_id("123456789012345678") == False  # 格式错误
    
    # 提取信息测试
    birth_date = IDCardValidator.extract_birth_date("11010119900307663X")
    assert birth_date is not None
    assert birth_date.year == 1990
    assert birth_date.month == 3
    assert birth_date.day == 7
    
    gender = IDCardValidator.extract_gender("11010119900307663X")
    assert gender == "男"

def test_registration_form():
    """测试注册表单"""
    # 测试有效表单数据
    form_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "phone": "13800138000",
        "agree_terms": True
    }
    
    response = client.post("/api/v1/auth/register", data=form_data)
    assert response.status_code == 200
    
    # 测试密码不匹配
    form_data["confirm_password"] = "Wrong@1234"
    response = client.post("/api/v1/auth/register", data=form_data)
    assert response.status_code == 422  # 验证错误
    
    # 测试未同意条款
    form_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "agree_terms": False
    }
    response = client.post("/api/v1/auth/register", data=form_data)
    assert response.status_code == 422

def test_login_form():
    """测试登录表单"""
    # 先注册用户
    register_data = {
        "username": "logintest",
        "email": "login@example.com",
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "agree_terms": True
    }
    client.post("/api/v1/auth/register", data=register_data)
    
    # 测试登录
    login_data = {
        "username": "logintest",
        "password": "Test@1234",
        "remember_me": True
    }
    response = client.post("/api/v1/auth/login/form", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # 测试错误密码
    login_data["password"] = "WrongPass"
    response = client.post("/api/v1/auth/login/form", data=login_data)
    assert response.status_code == 401

def test_item_form_with_images(tmp_path):
    """测试带图片的商品表单"""
    # 创建测试图片
    import os
    os.makedirs("uploads/images", exist_ok=True)
    
    # 准备表单数据
    form_data = {
        "title": "测试商品",
        "description": "这是一个测试商品",
        "price": 99.99,
        "category": "electronics",
        "tags": '["手机","数码"]'
    }
    
    # 准备测试文件
    files = [
        ("images", ("test1.jpg", b"fake image content", "image/jpeg")),
        ("images", ("test2.jpg", b"fake image content", "image/jpeg"))
    ]
    
    # 先登录获取token
    login_data = {
        "username": "testuser",
        "password": "Test@1234"
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # 测试创建商品
    response = client.post(
        "/api/v1/items/",
        data=form_data,
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "测试商品"
    assert len(response.json()["images"]) == 2