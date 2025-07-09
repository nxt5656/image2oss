import io
import oss2
import numpy as np
import requests
import torch
from PIL import Image, ImageOps, ImageSequence
from io import BytesIO

OSS_ENDPOINT_LIST = [
    # 中国内地
    "oss-cn-hangzhou.aliyuncs.com",
    "oss-cn-shanghai.aliyuncs.com",
    "oss-cn-qingdao.aliyuncs.com",
    "oss-cn-beijing.aliyuncs.com",
    "oss-cn-shenzhen.aliyuncs.com",
    "oss-cn-heyuan.aliyuncs.com",
    "oss-cn-zhangjiakou.aliyuncs.com",
    "oss-cn-huhehaote.aliyuncs.com",
    "oss-cn-wulanchabu.aliyuncs.com",
    "oss-cn-chengdu.aliyuncs.com",
    "oss-cn-hangzhou-internal.aliyuncs.com",
    "oss-cn-shanghai-internal.aliyuncs.com",
    "oss-cn-qingdao-internal.aliyuncs.com",
    "oss-cn-beijing-internal.aliyuncs.com",
    "oss-cn-shenzhen-internal.aliyuncs.com",
    "oss-cn-heyuan-internal.aliyuncs.com",
    "oss-cn-zhangjiakou-internal.aliyuncs.com",
    "oss-cn-huhehaote-internal.aliyuncs.com",
    "oss-cn-wulanchabu-internal.aliyuncs.com",
    "oss-cn-chengdu-internal.aliyuncs.com",
    # 中国香港
    "oss-cn-hongkong.aliyuncs.com",
    "oss-cn-hongkong-internal.aliyuncs.com",
    # 美国
    "oss-us-west-1.aliyuncs.com",
    "oss-us-east-1.aliyuncs.com",
    "oss-us-west-1-internal.aliyuncs.com",
    "oss-us-east-1-internal.aliyuncs.com",
    # 亚太
    "oss-ap-southeast-1.aliyuncs.com",
    "oss-ap-southeast-2.aliyuncs.com",
    "oss-ap-southeast-3.aliyuncs.com",
    "oss-ap-southeast-5.aliyuncs.com",
    "oss-ap-northeast-1.aliyuncs.com",
    "oss-ap-south-1.aliyuncs.com",
    "oss-ap-southeast-1-internal.aliyuncs.com",
    "oss-ap-southeast-2-internal.aliyuncs.com",
    "oss-ap-southeast-3-internal.aliyuncs.com",
    "oss-ap-southeast-5-internal.aliyuncs.com",
    "oss-ap-northeast-1-internal.aliyuncs.com",
    "oss-ap-south-1-internal.aliyuncs.com",
    # 欧洲
    "oss-eu-central-1.aliyuncs.com",
    "oss-eu-west-1.aliyuncs.com",
    "oss-eu-central-1-internal.aliyuncs.com",
    "oss-eu-west-1-internal.aliyuncs.com",
    # 中东
    "oss-me-east-1.aliyuncs.com",
    "oss-me-east-1-internal.aliyuncs.com"
]


# 将一个图像张量（Tensor）转换成 PIL (Pillow) 图像对象
def tensor_to_pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))


# Convert PIL to Tensor
def pil_to_tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

# 从url中获取图片
def read_image_from_url(image_url):
    try:
        # 1. 获取图片数据 (推荐开启 verify=True)
        response = requests.get(image_url, stream=True, timeout=15) # 增加超时时间
        response.raise_for_status() # 检查 HTTP 错误
        image_bytes = response.content

        # 2. 打开图片
        pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        # 3. 转换为 NumPy 数组并归一化
        numpy_image = np.array(pil_image).astype(np.float32) / 255.0

        # 4. 转换为 PyTorch 张量
        tensor_image = torch.from_numpy(numpy_image) # Shape: (H, W, C)

        # 5. 添加 Batch 维度
        batch_tensor = tensor_image.unsqueeze(0) # Shape: (1, H, W, C)

        # 6. 返回符合 ComfyUI 格式的张量
        return (batch_tensor,)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from URL: {e}")
        # 可以返回一个空的或者默认的图像张量，或者抛出异常
        # 返回空张量示例: return (torch.zeros((1, 64, 64, 3)),)
        raise Exception(f"Failed to load image from URL: {image_url}. Error: {e}") from e
    except Exception as e:
        print(f"Error processing image: {e}")
        raise Exception(f"Failed to process image from URL: {image_url}. Error: {e}") from e

# 上传图片到oss中
def put_object(file,filename,access_key_id, access_key_secret, security_token,bucket_name, endpoint):
    auth = oss2.StsAuth(access_key_id,access_key_secret,security_token,auth_version = "v2")
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    image_bytes = BytesIO()
    file.save(image_bytes, format='JPEG')  # 保存为 JPEG 格式
    image_bytes.seek(0)  # 将流指针回到开头

    try:
        bucket.put_object(filename, image_bytes)
        print(f'图片成功上传到 OSS，文件名为: {filename}')
    except oss2.exceptions.OssError as e:
        raise ValueError(f'上传失败，错误信息: {e}')

def put_object_for_cn_law(file,filename,access_key_id, access_key_secret, security_token,bucket_name, endpoint):
    f = add_watermark(file,text="Ai生成",font_path="ComfyUI/custom_nodes/image2oss/NotoSansCJKsc-Regular.otf")
    auth = oss2.StsAuth(access_key_id,access_key_secret,security_token,auth_version = "v2")
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    image_bytes = BytesIO()
    f.save(image_bytes, format='PNG')
    image_bytes.seek(0)  # 将流指针回到开头
    try:
        bucket.put_object(filename, image_bytes)
        print(f'图片成功上传到 OSS，文件名为: {filename}')
    except oss2.exceptions.OssError as e:
        raise ValueError(f'上传失败，错误信息: {e}')
    

# 从oss获取图片
def get_object(object_key, access_key_id, access_key_secret, security_token, bucket_name, endpoint):
    try:
        auth = oss2.StsAuth(access_key_id,access_key_secret,security_token,auth_version = "v2")
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        object_stream = bucket.get_object(object_key)
        img_data = object_stream.read()
        if not img_data:
            raise ValueError(f"Failed to read data for object: {object_key}")
        image = Image.open(io.BytesIO(img_data))
        image = image.convert("RGB")
        image_np = np.array(image).astype(np.float32)
        image_np /= 255.0

        # 如果图像不是灰度图，就拿一层出来充当蒙版，如果是灰度图，就直接使用
        if image_np.ndim == 3:
            mask_np = image_np[:, :, -1]
        else:
            mask_np = image_np
        
        image_tensor = torch.from_numpy(image_np)
        image_tensor = image_tensor.unsqueeze(0)

        mask_tensor = torch.from_numpy(mask_np)
        mask_tensor = mask_tensor.unsqueeze(0)
        print(f"Successfully loaded image from OSS. Tensor shape: {image_tensor.shape}")
        return (image_tensor, mask_tensor, )
    except oss2.exceptions.NoSuchKey:
        print(f"Error: Object '{object_key}' not found in bucket '{bucket_name}'.")
        # 可以选择返回一个空图像或默认图像，或者直接抛出异常
        # 这里我们重新抛出异常，让 ComfyUI 显示错误
        raise oss2.exceptions.NoSuchKey(f"Object '{object_key}' not found in bucket '{bucket_name}'.")
    except Exception as e:
        print(f"An error occurred while loading image from OSS: {e}")
        # 重新抛出异常，以便在 ComfyUI 中看到错误信息
        raise e
    finally:
        # 确保 response 被关闭 (oss2 的 get_object 返回的 stream 在 read() 后通常会自动处理，但显式关闭更安全)
        if 'object_stream' in locals() and hasattr(object_stream, 'resp') and object_stream.resp:
            # oss2 < 2.17.0: object_stream.resp.release_conn()
            # oss2 >= 2.17.0: object_stream.close()
            # 简单起见，如果 read() 成功，连接通常已关闭。如果读取失败或部分读取，则需要手动关闭。
            # Pillow 的 Image.open(io.BytesIO(img_data)) 处理的是内存数据，不涉及原始连接。
            # 如果直接用 Image.open(object_stream.resp)，则Pillow会负责读取和关闭。
            # 鉴于我们先 read() 了全部数据，这里通常不需要额外关闭。
            pass

# 从oss获取图片
def get_image_object(object_key, access_key_id, access_key_secret, security_token, bucket_name, endpoint):
    try:
        auth = oss2.StsAuth(access_key_id,access_key_secret,security_token,auth_version = "v2")
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        object_stream = bucket.get_object(object_key)
        img_data = object_stream.read()
        if not img_data:
            raise ValueError(f"Failed to read data for object: {object_key}")
        img = Image.open(io.BytesIO(img_data))
        output_images = []
        output_masks = []
        w, h = None, None

        excluded_formats = ["MPO"]

        for i in ImageSequence.Iterator(img):
            i = ImageOps.exif_transpose(i)

            if i.mode == "I":
                i = i.point(lambda i: i * (1 / 255))
            image = i.convert("RGB")

            if len(output_images) == 0:
                w = image.size[0]
                h = image.size[1]
            
            if image.size[0] != w or image.size[1] != h:
                continue

            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None, ]
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            output_images.append(image)
            output_masks.append(mask.unsqueeze(0))
            

        if len(output_images) > 1 and img.format not in excluded_formats:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]
        
        print(f"Successfully loaded image from OSS. Tensor shape: {output_image.shape}")
        return (output_image, output_mask)
    except oss2.exceptions.NoSuchKey:
        print(f"Error: Object '{object_key}' not found in bucket '{bucket_name}'.")
        # 可以选择返回一个空图像或默认图像，或者直接抛出异常
        # 这里我们重新抛出异常，让 ComfyUI 显示错误
        raise oss2.exceptions.NoSuchKey(f"Object '{object_key}' not found in bucket '{bucket_name}'.")
    except Exception as e:
        print(f"An error occurred while loading image from OSS: {e}")
        # 重新抛出异常，以便在 ComfyUI 中看到错误信息
        raise e
    finally:
        # 确保 response 被关闭 (oss2 的 get_object 返回的 stream 在 read() 后通常会自动处理，但显式关闭更安全)
        if 'object_stream' in locals() and hasattr(object_stream, 'resp') and object_stream.resp:
            # oss2 < 2.17.0: object_stream.resp.release_conn()
            # oss2 >= 2.17.0: object_stream.close()
            # 简单起见，如果 read() 成功，连接通常已关闭。如果读取失败或部分读取，则需要手动关闭。
            # Pillow 的 Image.open(io.BytesIO(img_data)) 处理的是内存数据，不涉及原始连接。
            # 如果直接用 Image.open(object_stream.resp)，则Pillow会负责读取和关闭。
            # 鉴于我们先 read() 了全部数据，这里通常不需要额外关闭。
            pass

# 从oss获取mask
def get_mask_object(object_key, access_key_id, access_key_secret, security_token, bucket_name, endpoint, channel):
    try:
        auth = oss2.StsAuth(access_key_id,access_key_secret,security_token,auth_version = "v2")
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        object_stream = bucket.get_object(object_key)
        img_data = object_stream.read()
        if not img_data:
            raise ValueError(f"Failed to read data for object: {object_key}")
        image = Image.open(io.BytesIO(img_data))
        image = ImageOps.exif_transpose(image)

        if image.getbands() != ("R", "G", "B", "A"):
            if image.mode == "I":
                image = image.point(lambda image: image * (1 / 255))
            image = image.convert("RGBA")

        mask = None
        c = channel[0].upper()
        if c in image.getbands():
            mask = np.array(image.getchannel(c)).astype(np.float32) / 255.0
            mask = torch.from_numpy(mask)
            if c == "A":
                mask = 1. - mask
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
        
        print(f"Successfully loaded image from OSS. Tensor shape: {mask.shape}")
        return (mask.unsqueeze(0), )
    except oss2.exceptions.NoSuchKey:
        print(f"Error: Object '{object_key}' not found in bucket '{bucket_name}'.")
        # 可以选择返回一个空图像或默认图像，或者直接抛出异常
        # 这里我们重新抛出异常，让 ComfyUI 显示错误
        raise oss2.exceptions.NoSuchKey(f"Object '{object_key}' not found in bucket '{bucket_name}'.")
    except Exception as e:
        print(f"An error occurred while loading image from OSS: {e}")
        # 重新抛出异常，以便在 ComfyUI 中看到错误信息
        raise e
    finally:
        # 确保 response 被关闭 (oss2 的 get_object 返回的 stream 在 read() 后通常会自动处理，但显式关闭更安全)
        if 'object_stream' in locals() and hasattr(object_stream, 'resp') and object_stream.resp:
            # oss2 < 2.17.0: object_stream.resp.release_conn()
            # oss2 >= 2.17.0: object_stream.close()
            # 简单起见，如果 read() 成功，连接通常已关闭。如果读取失败或部分读取，则需要手动关闭。
            # Pillow 的 Image.open(io.BytesIO(img_data)) 处理的是内存数据，不涉及原始连接。
            # 如果直接用 Image.open(object_stream.resp)，则Pillow会负责读取和关闭。
            # 鉴于我们先 read() 了全部数据，这里通常不需要额外关闭。
            pass


# 获取阿里云ak信息
def get_aliyun_ak(sts_service_url):
    try:
        response = requests.get(sts_service_url)
        response.raise_for_status()
        data = response.json()
        if not data["success"]:
            raise ValueError(f"获取ak失败: {data}")
        return data
    except requests.exceptions.HTTPError as http_err:
        raise ValueError(f"HTTP 错误发生: {http_err}")
    except requests.exceptions.RequestException as req_err:
        raise ValueError(f"请求错误发生: {req_err}")
    except ValueError as value_err:
        raise ValueError(f"JSON 解析错误: {value_err}")

def upload_image_to_oss(image, filename, sts_service_url, bucket_name, endpoint):
    """
    上传图片到阿里云OSS
    :param image: PIL Image对象
    :param filename: 上传到OSS的文件名
    :param sts_service_url: 获取临时STS凭证的服务URL
    :param bucket_name: OSS存储桶名称
    :param endpoint: OSS服务的Endpoint
    """
    data = get_aliyun_ak(sts_service_url)
    access_key_id = data["data"]["accessKeyId"]
    access_key_secret = data["data"]["accessKeySecret"]
    security_token = data["data"]["securityToken"]

    put_object(image, filename, access_key_id, access_key_secret, security_token, bucket_name, endpoint)

def add_watermark(img, text="AI生成", font_path=None):
    img = img.convert("RGBA")
    """
    为图片添加水印，水印位于右下角，文字高度不低于画面最短边长度的5%。

    Args:
        image_path (str): 原始图片的路径。
        text (str): 水印文字内容，默认为"AI生成"。
        font_path (str, optional): 字体文件的路径。如果为None，将尝试使用默认字体。
                                   建议提供一个中文字体路径，否则中文字符可能无法正常显示。
    Returns:
        PIL.Image.Image: 添加水印后的图片对象。
    """
    try:
        draw = ImageDraw.Draw(img)
    except Exception as e :
        print(e)
        return
    img_width, img_height = img.size

    # 计算最短边长度
    min_side = min(img_width, img_height)

    # 最小水印文字高度（最短边长度的5%）
    min_watermark_height = int(min_side * 0.05)
    if min_watermark_height < 10:  # 确保字体不会太小
        min_watermark_height = 10

    # 尝试加载字体
    # 如果没有指定字体路径，尝试使用系统默认字体或者常见的字体名称
    # 推荐使用像 'arial.ttf', 'simhei.ttf', 'msyh.ttc' 等中文字体
    try:
        if font_path and os.path.exists(font_path):
            print(font_path)
            print(os.path.exists(font_path))
            # 尝试不同的字体大小直到达到最小高度
            font_size = 1
            font = ImageFont.truetype(font_path, font_size)
            while True:
                # 使用textbbox来获取更准确的文本框大小
                bbox = draw.textbbox((0, 0), text, font=font)
                text_height = bbox[3] - bbox[1] # height = y2 - y1

                if text_height >= min_watermark_height:
                    break
                font_size += 1
                font = ImageFont.truetype(font_path, font_size)
                # 避免无限循环，设置一个最大字体大小
                if font_size > max(img_width, img_height) // 2:
                    print(f"警告：无法找到满足最小高度 {min_watermark_height} 的字体大小，使用当前最大字体大小 {font_size}")
                    break
        else:
            # 如果没有提供字体路径或字体文件不存在，尝试默认字体
            # 这通常只适用于英文字符，中文字符可能显示为方块
            print("警告：未提供有效的字体路径或字体文件不存在。尝试使用默认字体，中文字符可能无法正常显示。")
            font_size = min_watermark_height
            font = ImageFont.load_default() # 对于中文字符，这个可能无法很好地工作
            # 再次尝试调整大小以匹配最小高度
            # 针对load_default()的特殊处理，因为其无法直接通过参数调整大小
            # 这里的调整可能不精确，但在没有中文字体时是权宜之计
            while True:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_height = bbox[3] - bbox[1]
                if text_height >= min_watermark_height:
                    break
                # load_default() 无法调整大小，只能通过其他方式来模拟
                # 这里为了演示，我们假设load_default()有某种机制能间接调整大小，实际并非如此
                # 更好的做法是强制用户提供一个中文字体
                font_size += 1
                if font_size > max(img_width, img_height) // 2:
                    break
                # 注意：这里没有真正改变load_default()的字体大小，这是个限制
                # 实际应用中必须使用truetype加载自定义大小的字体

    except IOError:
        print(f"错误：无法加载字体文件 '{font_path}'。请确保路径正确且文件可读。")
        print("尝试使用PIL的默认字体，中文字符可能无法正常显示。")
        font = ImageFont.load_default()
        # 尝试调整大小以满足最小高度（可能不精确）
        font_size = min_watermark_height
        while True:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_height = bbox[3] - bbox[1]
            if text_height >= min_watermark_height:
                break
            font_size += 1
            if font_size > max(img_width, img_height) // 2:
                break
            # 同样，这里对load_default()的字体大小调整是模拟的，不精确

    except Exception as e:
        print(f"加载字体时发生错误：{e}")
        print("尝试使用PIL的默认字体，中文字符可能无法正常显示。")
        font = ImageFont.load_default()
        font_size = min_watermark_height
        while True:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_height = bbox[3] - bbox[1]
            if text_height >= min_watermark_height:
                break
            font_size += 1
            if font_size > max(img_width, img_height) // 2:
                break


    # 获取水印文字的实际大小
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 设置边距
    margin = int(min_side * 0.02)  # 2%的边距

    # 计算水印位置 (右下角)
    x = img_width - text_width - margin
    y = img_height - text_height - margin

    # 设置水印颜色和透明度 (RGBA)
    watermark_color = (255, 255, 255, 50)  # 黑色，半透明

    # 添加水印
    draw.text((x, y), text, font=font, fill=watermark_color)

    return img



if __name__ == "__main__":
    image_list = [
        "image1.png",
        "image2.png",
        "image3.png"
    ]

    for image_file in image_list:
        try:
            # 读取图片
            image = Image.open(image_file)
            # 上传到OSS
            upload_image_file = f"devops/comfyui/input/{image_file}"
            upload_image_to_oss(image, upload_image_file, "https://devops-id.zhiyitech.cn/api/auth/sts/zhiyi-fd-comfyui?key=ygRYPXhJCc5ZV8Q2s4FLSk", "zhiyi-image", "oss-cn-hangzhou.aliyuncs.com")
            print(f"成功上传 {image_file} 到 OSS")
        except Exception as e:
            print(f"上传 {image_file} 失败: {e}")