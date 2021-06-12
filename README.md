# Django TencentCOS Storage

腾讯云对象存储（COS）服务 for Django。

## 环境要求

Python: >=3.7, <4

Django: >=2.2, <3.3

## 安装

```
pip install django-tencentcos-storage
```

## 基本使用

在项目的 settings.py 中设置 `DEFAULT_FILE_STORAGE`：

```python
DEFAULT_FILE_STORAGE = "tencentcos_storage.TencentCOSStorage"
```

此外，还需要设置腾讯云对象存储服务相关的必要信息：

```python
TENCENTCOS_STORAGE = {
    "BUCKET": "存储桶名称",
    "CONFIG": {
        "Region": "地域信息",
        "SecretId": "密钥 SecretId",
        "SecretKey": "密钥 SecretKey",
    }
}
```

详情可参考 [腾讯云对象存储官方文档](https://cloud.tencent.com/document/product/436)

## 设置

### 示例
```python
TENCENTCOS_STORAGE = {
    # 存储桶名称，必填
    "BUCKET": "存储桶名称",
    # 存储桶文件根路径，默认 '/'
    "ROOT_PATH": "/",
    # 腾讯云存储 Python SDK 的配置参数，详细说明请参考腾讯云官方文档
    "CONFIG": {
        "Region": "地域信息",
        "SecretId": "密钥 SecretId",
        "SecretKey": "密钥 SecretKey",
    }
}
```

### 说明

**BUCKET**
> 存储桶名称，必填

**ROOT_PATH**
> 文件根路径，默认为 '/'

**CONFIG**
> 腾讯云对象存储 Python SDK 的配置参数，其中 `Region`、`SecretId`、`SecretKey` 为必填参数。
> 
> 关于配置参数的详细说明请参考 [腾讯云对象存储 Python SDK 官方文档](https://cloud.tencent.com/document/product/436/12269)

