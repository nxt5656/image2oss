from .util import tensor_to_pil,read_image_from_url,put_object,get_aliyun_ak,OSS_ENDPOINT_LIST,get_object, get_image_object, get_mask_object, put_object_for_cn_law
from comfy.cli_args import args
import ast

class OSSUploadNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "filename": ("STRING",{"default":'["tmp-comfyui/filename.jpeg"]'}),
                "access_key_id": ("STRING", {"default": "access_key_id"}),
                "access_key_secret": ("STRING", {"default": "access_key_secret"}),
                "security_token": ("STRING", {"default": ""}),
                "bucket_name": ("STRING", {"default": "bucket_name"}),
                "endpoint": (OSS_ENDPOINT_LIST,{"default": "oss-cn-hangzhou.aliyuncs.com"}),
            }
        }

    # 校验参数是否正确
    @classmethod
    def VALIDATE_INPUTS(cls,image, filename, access_key_id, access_key_secret, bucket_name, endpoint):
        #print("参数校验:\t%s,%s,%s,%s,%s" % (filename, access_key_id, access_key_secret, bucket_name, endpoint))
        if filename == "" or access_key_id == "" or access_key_secret == "" or bucket_name == "" or endpoint == "":
            return "参数不能为空"
        # 检查endpoing
        if endpoint not in OSS_ENDPOINT_LIST:
            return "endpoint 不正确\t %s" % endpoint
        return True
    RETURN_TYPES = ()
    FUNCTION = "upload_to_oss"
    CATEGORY = "API/oss"
    OUTPUT_NODE = True
    
    def upload_to_oss(self, image, filename, access_key_id, access_key_secret,security_token, bucket_name, endpoint):
        #print("参数信息: \t%s,%s,%s,%s,%s\n" %( filename,access_key_id, access_key_secret, bucket_name, endpoint))

        # 先判断这里是不是字符串
        if not isinstance(filename, str):
            raise ValueError("文件名必须为列表")
        try:
            filenameList = ast.literal_eval(filename)
            if isinstance(filenameList, list):  # 检查解析后的结果是否是列表
                pass
            else:
                raise ValueError("文件名必须为列表")
        except:
            raise ValueError("文件名必须为列表")
        print("共有图片[%s]张,filename[%s]个\n" % (len(image), len(filenameList) ))
        if len(image)!= len(filenameList) :
            raise ValueError("生成图片数量与给定的文件名数量不对应")
        n = 0
        results = []
        for i in image:
            img = tensor_to_pil(i)
            #print("文件名称: [%s] \t文件类型: %s" % (filenameList[n],type(img)))
            put_object(img,filenameList[n],access_key_id, access_key_secret, security_token,bucket_name, endpoint)
            print("上传图片[%s]到oss成功" % filenameList[n])
            results.append({
                "filename": filenameList[n],
                "type": "output",
            })
            n = n + 1


        return {"ui": {"images": results}}

def save_image_local(image, filename):
    """
    保存图片到本地
    :param image: 图片张量
    :param filename: 文件名
    :return: None
    """
    if not isinstance(filename, str):
        raise ValueError("文件名必须为字符串")
    image.save(filename)
    print(f"图片已保存到本地: {filename}")

class OSSUploadNodeBySTSServiceUrl:

    def __init__(self):
        self.base_result_folder = "devops/comfyui/output/"
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING",{"default":'["tmp-comfyui/filename.jpeg"]'}),
                "sts_service_url": ("STRING", {"default": "https://demo.cn/sts_service"}),
                "bucket_name": ("STRING", {"default": "bucket_name"}),
                "endpoint": (OSS_ENDPOINT_LIST,{"default": "oss-cn-hangzhou.aliyuncs.com"}),
            }
        }
        # 校验参数是否正确
    
    @classmethod
    def VALIDATE_INPUTS(cls,images, filename_prefix, sts_service_url, bucket_name, endpoint):
        print("参数校验:\t%s,%s,%s,%s" % (filename_prefix, sts_service_url, bucket_name, endpoint))
        if filename_prefix == "" or sts_service_url == "" or bucket_name == "" or endpoint == "":
            return "参数不能为空"
        # 检查endpoing
        if endpoint not in OSS_ENDPOINT_LIST:
            return "endpoint 不正确\t %s" % endpoint
        return True
    RETURN_TYPES = ()
    FUNCTION = "upload_to_oss"
    CATEGORY = "API/oss"
    OUTPUT_NODE = True
    def upload_to_oss(self, images, filename_prefix, sts_service_url, bucket_name, endpoint):
        #print("参数信息: \t%s,%s,%s,%s,%s\n" %( filename,access_key_id, access_key_secret, bucket_name, endpoint))

        # 先判断这里是不是字符串
        # if not isinstance(filename, str):
        #     raise ValueError("文件名必须为列表")
        # try:
        #     filenameList = ast.literal_eval(filename)
        #     if isinstance(filenameList, list):  # 检查解析后的结果是否是列表
        #         pass
        #     else:
        #         raise ValueError("文件名必须为列表")
        # except:
        #     raise ValueError("文件名必须为列表")
        # print("共有图片[%s]张,filename[%s]个\n" % (len(image), len(filenameList) ))


        # if len(image)!= len(filenameList) :
        #     raise ValueError("生成图片数量与给定的文件名数量不对应")


        data = get_aliyun_ak(sts_service_url)
        access_key_id = data["data"]["accessKeyId"]
        access_key_secret = data["data"]["accessKeySecret"]
        security_token = data["data"]["securityToken"]

        results = []
        n = 1
        for i in images:
            img = tensor_to_pil(i)
            filename = f"{filename_prefix}_{n}.png"
            # file_folder = "/root/ComfyUI/output"
            # resut_filename = f"{file_folder}/{filename}"
            # save_image_local(img, resut_filename)
            upload_filename = f"{self.base_result_folder}{filename}"
            put_object(img, upload_filename, access_key_id, access_key_secret, security_token, bucket_name, endpoint)
            n = n + 1
            results.append({
                "filename": filename,
                "type": self.type
            })

        return { "ui": { "images": results } }


class LoadImageFromURL:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_url": ("STRING",{"default":"https://picsum.photos/200/300"}),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "load_image"
    CATEGORY = "API/oss"
    def load_image(self, image_url):
        return read_image_from_url(image_url)

class LoadImageFromOss:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "filename": ("STRING",{"default":"tmp/screenshot.png"}),
                "access_key_id": ("STRING", {"default": "access_key_id"}),
                "access_key_secret": ("STRING", {"default": "access_key_secret"}),
                "security_token": ("STRING", {"default": ""}),
                "bucket_name": ("STRING", {"default": "bucket_name"}),
                "endpoint": (OSS_ENDPOINT_LIST,{"default": "oss-cn-hangzhou.aliyuncs.com"}),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    CATEGORY = "API/oss"
    FUNCTION = "load_image"
    def load_image(self, filename, access_key_id, access_key_secret, security_token, bucket_name, endpoint):
        return get_object(filename, access_key_id, access_key_secret, security_token, bucket_name, endpoint)


class LoadImageFromOssBySTSServiceUrl:
    
    def __init__(self):
        self.base_load_folder = "devops/comfyui/input/"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "filename": ("STRING",{"default":"tmp-comfyui/filename.jpeg"}),
                "sts_service_url": ("STRING", {"default": "https://demo.cn/sts_service"}),
                "bucket_name": ("STRING", {"default": "bucket_name"}),
                "endpoint": (OSS_ENDPOINT_LIST,{"default": "oss-cn-hangzhou.aliyuncs.com"}),
            }
        }
    RETURN_TYPES = ("IMAGE", "MASK", )
    CATEGORY = "API/oss"
    FUNCTION = "load_image"
    def load_image(self, filename, sts_service_url,  bucket_name, endpoint):
        load_filename = f"{filename}"

        data = get_aliyun_ak(sts_service_url)
        access_key_id = data["data"]["accessKeyId"]
        access_key_secret = data["data"]["accessKeySecret"]
        security_token = data["data"]["securityToken"]
        return get_image_object(load_filename, access_key_id, access_key_secret, security_token, bucket_name, endpoint)

class LoadMaskFromOssBySTSServiceUrl:
    
    color_channels = ["alpha", "red", "green", "blue"]
    def __init__(self):
        self.base_load_folder = "devops/comfyui/input/"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "filename": ("STRING",{"default":"tmp-comfyui/filename.jpeg"}),
                "sts_service_url": ("STRING", {"default": "https://demo.cn/sts_service"}),
                "bucket_name": ("STRING", {"default": "bucket_name"}),
                "endpoint": (OSS_ENDPOINT_LIST,{"default": "oss-cn-hangzhou.aliyuncs.com"}),
                "channel": (cls.color_channels, ),
            }
        }
    RETURN_TYPES = ("MASK", )
    CATEGORY = "API/oss"
    FUNCTION = "load_image"
    def load_image(self, filename, sts_service_url,  bucket_name, endpoint, channel):
        load_filename = f"{filename}"

        data = get_aliyun_ak(sts_service_url)
        access_key_id = data["data"]["accessKeyId"]
        access_key_secret = data["data"]["accessKeySecret"]
        security_token = data["data"]["securityToken"]
        return get_mask_object(load_filename, access_key_id, access_key_secret, security_token, bucket_name, endpoint, channel)

# 保存图片到oss,通过阿里云sdk,使用ak/sk,中国法律要求aigc内容必须添加ai标记
class OSSUploadNodeForCNLaw:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "filename": ("STRING",{"default":'["tmp-comfyui/filename.jpeg"]'}),
                "access_key_id": ("STRING", {"default": "access_key_id"}),
                "access_key_secret": ("STRING", {"default": "access_key_secret"}),
                "security_token": ("STRING", {"default": ""}),
                "bucket_name": ("STRING", {"default": "bucket_name"}),
                "endpoint": (OSS_ENDPOINT_LIST,{"default": "oss-cn-hangzhou.aliyuncs.com"}),
            }
        }

        # 校验参数是否正确
    @classmethod
    def VALIDATE_INPUTS(cls,image, filename, access_key_id, access_key_secret, bucket_name, endpoint):
        #print("参数校验:\t%s,%s,%s,%s,%s" % (filename, access_key_id, access_key_secret, bucket_name, endpoint))
        if filename == "" or access_key_id == "" or access_key_secret == "" or bucket_name == "" or endpoint == "":
            return "参数不能为空"
        # 检查endpoing
        if endpoint not in OSS_ENDPOINT_LIST:
            return "endpoint 不正确\t %s" % endpoint
        return True
    RETURN_TYPES = ()
    FUNCTION = "upload_to_oss"
    CATEGORY = "API/oss"
    OUTPUT_NODE = True
    def upload_to_oss(self, image, filename, access_key_id, access_key_secret,security_token, bucket_name, endpoint):
        #print("参数信息: \t%s,%s,%s,%s,%s\n" %( filename,access_key_id, access_key_secret, bucket_name, endpoint))

        # 先判断这里是不是字符串
        if not isinstance(filename, str):
            raise ValueError("文件名必须为列表")
        try:
            filenameList = ast.literal_eval(filename)
            if isinstance(filenameList, list):  # 检查解析后的结果是否是列表
                pass
            else:
                raise ValueError("文件名必须为列表")
        except:
            raise ValueError("文件名必须为列表")
        print("共有图片[%s]张,filename[%s]个\n" % (len(image), len(filenameList) ))
        if len(image)!= len(filenameList) :
            raise ValueError("生成图片数量与给定的文件名数量不对应")
        n = 0
        for i in image:
            img = tensor_to_pil(i)
            #print("文件名称: [%s] \t文件类型: %s" % (filenameList[n],type(img)))
            put_object_for_cn_law(img,filenameList[n],access_key_id, access_key_secret, security_token,bucket_name, endpoint)
            n = n + 1

        return ()


# 保存图片到oss,通过阿里云sdk,使用自建sts服务,中国法律要求aigc内容必须添加ai标记
class OSSUploadNodeBySTSServiceUrlForCNLaw:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "filename": ("STRING",{"default":'["tmp/002/001.jpeg"]'}),
                "sts_service_url": ("STRING", {"default": "https://demo.cn/sts_service"}),
                "bucket_name": ("STRING", {"default": "bucket_name"}),
                "endpoint": (OSS_ENDPOINT_LIST,{"default": "oss-cn-hangzhou.aliyuncs.com"}),
            }
        }
        # 校验参数是否正确
    @classmethod
    def VALIDATE_INPUTS(cls,image, filename, sts_service_url, bucket_name, endpoint):
        print("参数校验:\t%s,%s,%s,%s" % (filename, sts_service_url, bucket_name, endpoint))
        if filename == "" or sts_service_url == "" or bucket_name == "" or endpoint == "":
            return "参数不能为空"
        # 检查endpoing
        if endpoint not in OSS_ENDPOINT_LIST:
            return "endpoint 不正确\t %s" % endpoint
        return True
    RETURN_TYPES = ()
    FUNCTION = "upload_to_oss"
    CATEGORY = "API/oss"
    OUTPUT_NODE = True
    def upload_to_oss(self, image, filename, sts_service_url, bucket_name, endpoint):
        #print("参数信息: \t%s,%s,%s,%s,%s\n" %( filename,access_key_id, access_key_secret, bucket_name, endpoint))

        # 先判断这里是不是字符串
        if not isinstance(filename, str):
            raise ValueError("文件名必须为列表")
        try:
            filenameList = ast.literal_eval(filename)
            if isinstance(filenameList, list):  # 检查解析后的结果是否是列表
                pass
            else:
                raise ValueError("文件名必须为列表")
        except:
            raise ValueError("文件名必须为列表")
        print("共有图片[%s]张,filename[%s]个\n" % (len(image), len(filenameList) ))
        if len(image)!= len(filenameList) :
            raise ValueError("生成图片数量与给定的文件名数量不对应")
        data = get_aliyun_ak(sts_service_url)
        access_key_id = data["data"]["accessKeyId"]
        access_key_secret = data["data"]["accessKeySecret"]
        security_token = data["data"]["securityToken"]

        n = 0
        for i in image:
            img = tensor_to_pil(i)
            put_object_for_cn_law(img,filenameList[n],access_key_id, access_key_secret, security_token,bucket_name, endpoint)
            n = n + 1

        return ()


NODE_CLASS_MAPPINGS = {
    "OSSUploadNode": OSSUploadNode,
    "OSSUploadNodeForCNLaw": OSSUploadNodeForCNLaw,
    "OSSUploadNodeBySTSServiceUrl": OSSUploadNodeBySTSServiceUrl,
    "OSSUploadNodeBySTSServiceUrlForCNLaw": OSSUploadNodeBySTSServiceUrlForCNLaw,
    "LoadImageFromURL": LoadImageFromURL,
    "LoadImageFromOss":LoadImageFromOss,
    "LoadImageFromOssBySTSServiceUrl":LoadImageFromOssBySTSServiceUrl,
    "LoadMaskFromOssBySTSServiceUrl": LoadMaskFromOssBySTSServiceUrl,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OSSUploadNode": "保存图片到oss",
    "OSSUploadNodeBySTSServiceUrl": "保存图片到oss(使用服务获取ak信息)",
    "LoadImageFromURL":"从url加载图片",
    "OSSUploadNodeForCNLaw": "image2oss-tag",
    "OSSUploadNodeBySTSServiceUrlForCNLaw": "image2oss-tag-sts-service",
    "LoadImageFromOss":"从oss加载图片",
    "LoadImageFromOssBySTSServiceUrl":"从oss加载图片(使用服务获取ak信息)",
    "LoadMaskFromOssBySTSServiceUrl":"从oss加载mask(使用服务获取ak信息)",
}