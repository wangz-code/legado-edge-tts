#!/usr/bin/env python3
import asyncio
from aiohttp import web
import edge_tts
import re
from urllib.parse import unquote
import json
import uuid
import random
from pathlib import Path
from typing import Optional, AsyncGenerator, Dict, Any
import time
import base64
try:
    import websockets
except ImportError:
    print("请安装 websockets: pip install websockets")
    exit(1)

def remove_special_characters(text):
    text = unquote(text)
    return re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：、（）《》【】“”‘’]', '', text)

def generate_16bytes_base64():
    """
    生成 16 字节随机数的 Base64 编码字符串（和示例格式一致）
    返回：符合要求的 Base64 字符串（如 oBxYeqcEenrw1pL64V3ieg==）
    """
    # 1. 生成 16 字节随机二进制数据（UUID v4 正好是 16 字节，符合示例特征）
    random_16bytes = uuid.uuid4().bytes
    
    # 2. 进行标准 Base64 编码（自动补充 == 填充符）
    base64_str = base64.b64encode(random_16bytes).decode('utf-8')
    
    return base64_str


async def generate_audio_edge(request):
    try:
        # 解析表单数据
        form = await request.post()
        text = form.get('text', '')
        voice = form.get('voice', 'zh-CN-XiaoxiaoNeural')
        rate = form.get('rate', '0')
        cookie=form.get('cookie','')
        
        # 处理文本
        cleaned_text = remove_special_characters(text)
        
        # 处理语速
        try:
            rate_value = max(0, min(100, int(rate)))
        except ValueError:
            rate_value = 25
            
        rate_offset = rate_value - 25
        custom_rate = f"+{rate_offset}%" if rate_offset > 0 else f"{rate_offset}%"
        
        # 创建流式响应
        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'audio/mpeg',
                'Content-Disposition': 'attachment; filename=audio.mp3'
            }
        )
        await response.prepare(request)
        
        # 流式生成音频并发送
        communicate = edge_tts.Communicate(cleaned_text, voice, rate=custom_rate)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                await response.write(chunk["data"])
                
        await response.write_eof()
        return response
        
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def generate_audio_doubao(request):
    try:
        # 解析表单数据
        form = await request.post()
        text = form.get('text', '')
        voice = form.get('voice', 'taozi')
        rate = form.get('rate', '0')
        cookie=form.get('cookie','')
        # 处理文本
        cleaned_text = remove_special_characters(text)
        # 处理语速
        try:
            rate_value = max(0, min(100, int(rate)))
        except ValueError:
            rate_value = 25
            
        rate_offset = rate_value - 25
        custom_rate = f"+{rate_offset}%" if rate_offset > 0 else f"{rate_offset}%"
        
        # 创建流式响应
        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'audio/mpeg',
                'Content-Disposition': 'attachment; filename=audio.mp3'
            }
        )
        await response.prepare(request)
        
        # 流式生成音频并发送
        CUSTOM_RATE = 0  # 语速正常 语速 (-1.0 ~ 1.0)
        # 创建TTS实例
        tts = DoubaoTTS()
        
        # 流式生成音频（模拟Web响应场景）
        try:
            async for chunk in tts.gen_audio(cookie, cleaned_text, voice, rate=CUSTOM_RATE):
                if chunk["type"] == "audio":
                    # 这里可以将音频块写入响应流（如FastAPI/Starlette的Response）
                    await response.write(chunk["data"])
                    # print(f"收到音频块，大小: {len(chunk['data'])} bytes")
                elif chunk["type"] == "error":
                    print(f"错误: {chunk['data']}")
                elif chunk["type"] == "info":
                    print(f"信息: {chunk['data']}")
        except Exception as e:
            print(f"生成音频失败: {e}")

        await response.write_eof()
        return response
        
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)




# 常用语音角色
SPEAKERS = {
    # 女声
    "taozi": "zh_female_taozi_conversation_v4_wvae_bigtts",  # 桃子 - 对话
    "shuangkuai": "zh_female_shuangkuai_emo_v3_wvae_bigtts",  # 爽快
    "tianmei": "zh_female_tianmei_conversation_v4_wvae_bigtts",  # 甜美
    "qingche": "zh_female_qingche_moon_bigtts",  # 清澈
    
    # 男声
    "yangguang": "zh_male_yangguang_conversation_v4_wvae_bigtts",  # 阳光
    "chenwen": "zh_male_chenwen_moon_bigtts",  # 沉稳
    "rap": "zh_male_rap_mars_bigtts",  # 说唱
    
    # 多语言
    "en_female": "en_female_sarah_conversation_bigtts",
    "en_male": "en_male_adam_conversation_bigtts",
}


class DoubaoTTS:
    """豆包 TTS 客户端"""
    WS_URL = "wss://ws-samantha.doubao.com/samantha/audio/tts"
    def __init__(self):
        self._device_id = self._generate_device_id()
        self._web_id = self._generate_web_id()
    
    def _generate_device_id(self) -> str:
        """生成设备 ID"""
        return str(random.randint(7400000000000000000, 7499999999999999999))
    
    def _generate_web_id(self) -> str:
        """生成 Web ID"""
        return str(random.randint(7400000000000000000, 7499999999999999999))
    
    def _build_ws_url(self, speaker: str, format: str = "aac", speed: float = 0, pitch: float = 0) -> str:
        """构建 WebSocket URL"""
        # 解析音色（支持简称或完整ID）
        speaker_id = SPEAKERS.get(speaker, speaker)
        
        params = {
            "speaker": speaker_id,
            "format": format,
            "speech_rate": int(speed * 100) if speed != 0 else 0,
            "pitch": int(pitch * 100) if pitch != 0 else 0,
            "version_code": 20800,
            "language": "zh",
            "device_platform": "web",
            "aid": 497858,
            "real_aid": 497858,
            "pkg_type": "release_version",
            "device_id": self._device_id,
            "pc_version": "2.51.7",
            "web_id": self._web_id,
            "tea_uuid": self._web_id,
            "region": "CN",
            "sys_region": "CN",
            "samantha_web": 1,
            "use-olympus-account": 1,
            "web_tab_id": str(uuid.uuid4()),
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.WS_URL}?{query}"
    
    async def gen_audio(
        self,
        cookie: str,
        text: str,
        voice: str,
        rate: float = 0.0,
        pitch: float = 0.0,
        format: str = "aac"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成音频（异步生成器）
        :param cookie: 豆包Cookie
        :param text: 要转换的文本
        :param voice: 音色（支持简称如taozi，或完整ID）
        :param rate: 语速 (-1.0 ~ 1.0)，0为正常
        :param pitch: 音调 (-1.0 ~ 1.0)，0为正常
        :param format: 音频格式，默认aac
        :yield: 字典，包含 type (audio/info/error) 和 data
        """
        if not cookie:
            yield {"type": "error", "data": "Cookie不能为空"}
            return
        
        if not text:
            yield {"type": "error", "data": "转换文本不能为空"}
            return
        
        ws_url = self._build_ws_url(voice, format, rate, pitch)
        print("ws_url",ws_url)
        headers = {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Origin": "https://www.doubao.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Sec-WebSocket-Version": 13,
            "Sec-WebSocket-Key": generate_16bytes_base64(),
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits"
            # "Cookie": cookie
        }
        
        try:
            async with websockets.connect(
                ws_url,
                additional_headers=headers,
            ) as ws:
                # 发送文本
                await ws.send(json.dumps({
                    "event": "text",
                    "text": text
                }))
                
                # 发送结束信号
                await ws.send(json.dumps({
                    "event": "finish"
                }))
                
                yield {"type": "info", "data": "连接成功，开始生成音频"}
                
                # 接收响应
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=30)
                        
                        if isinstance(message, bytes):
                            # 音频数据块
                            yield {"type": "audio", "data": message}
                        else:
                            # JSON 消息
                            data = json.loads(message)
                            event = data.get("event", "")
                            
                            if event == "open_success":
                                yield {"type": "info", "data": "WebSocket连接成功"}
                                
                            elif event == "sentence_start":
                                readable_text = data.get("sentence_start_result", {}).get("readable_text", "")
                                yield {"type": "info", "data": f"开始合成句子: {readable_text[:50]}..."}
                                
                            elif event == "error":
                                error_msg = data.get("message", "未知错误")
                                yield {"type": "error", "data": error_msg}
                                break
                                
                            elif data.get("code", 0) != 0:
                                error_msg = f"错误码 {data.get('code')}: {data.get('message', '未知错误')}"
                                yield {"type": "error", "data": error_msg}
                                break
                                
                    except asyncio.TimeoutError:
                        yield {"type": "info", "data": "接收超时，音频合成完成"}
                        break
                    except websockets.exceptions.ConnectionClosed:
                        yield {"type": "info", "data": "连接关闭，音频合成完成"}
                        break
                        
        except Exception as e:
            yield {"type": "error", "data": f"连接失败: {str(e)}"}
            return


# 便捷函数：生成完整音频文件
async def generate_audio_file(
    cookie: str,
    text: str,
    voice: str,
    output_path: str = "output.aac",
    rate: float = 0.0,
    pitch: float = 0.0,
    format: str = "aac"
) -> bool:
    """
    生成完整的音频文件
    :param cookie: 豆包Cookie
    :param text: 转换文本
    :param voice: 音色
    :param output_path: 输出文件路径
    :param rate: 语速
    :param pitch: 音调
    :param format: 音频格式
    :return: 是否成功
    """
    tts = DoubaoTTS()
    audio_chunks = []
    success = True
    
    async for chunk in tts.gen_audio(cookie, text, voice, rate, pitch, format):
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "error":
            print(f"[ERROR] {chunk['data']}")
            success = False
        elif chunk["type"] == "info":
            print(f"[INFO] {chunk['data']}")
    
    if success and audio_chunks:
        output = Path(output_path)
        output.write_bytes(b"".join(audio_chunks))
        print(f"\n✅ 音频已保存到: {output.absolute()}")
        print(f"   文件大小: {len(b''.join(audio_chunks)):,} bytes")
        return True
    return False




app = web.Application()
app.router.add_post('/api/rap', generate_audio_edge)
app.router.add_post('/api/doubao', generate_audio_doubao)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=1233)