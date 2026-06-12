#!/usr/bin/env python3
import asyncio
from aiohttp import web
import edge_tts
import re
from urllib.parse import unquote
import base64
import requests
import hashlib
import wave
import struct
from openai import OpenAI

MIMO_API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
MIMO_OPEN_URL = "https://api.xiaomimimo.com/v1"
MIMO_API_KEY = "这里替换为你的api-key" # sk-xxxxxxx


def remove_special_characters(text):
    text = unquote(text)
    return re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：、（）《》【】“”‘’]', '', text)

async def generate_audio(request):
    try:
        # 解析表单数据
        form = await request.post()
        text = form.get('text', '')
        voice = form.get('voice', 'zh-CN-XiaoxiaoNeural')
        rate = form.get('rate', '0')
        
        # 处理文本
        cleaned_text = remove_special_characters(text)
        
        # 处理语速
        try:
            rate_value = max(0, min(100, int(rate)))
        except ValueError:
            rate_value = 25
            
        rate_offset = rate_value - 25
        custom_rate = f"+{rate_offset}%" if rate_offset > 0 else f"{rate_offset}%"
        
        uid = hashlib.md5(cleaned_text.encode("utf-8")).hexdigest()[:12]
        # 创建流式响应
        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'audio/mpeg',
                'Content-Disposition':  f'attachment; filename="audio_{uid}.mp3"',
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



# 小米 mimo
async def generate_mimoaudio(request):
    try:
        form = await request.post()
        text = form.get('text', '')
        voice = form.get('voice', 'Chloe')
        rate = form.get('rate', '0')
        style = form.get("style", "自然、口语化的对话语调")

        cleaned_text = remove_special_characters(text)
        try:
            rate_value = max(0, min(100, int(rate)))
        except ValueError:
            rate_value = 25

        diff = rate_value - 25
        if diff <= -15:
            pace = "非常慢的语速"
        elif diff <= -5:
            pace = "偏慢的语速"
        elif diff >= 15:
            pace = "非常快的语速"
        elif diff >= 5:
            pace = "偏快的语速"
        else:
            pace = "正常语速"
        cur_style = f"{style}，{pace}"


        uid = hashlib.md5(cleaned_text.encode("utf-8")).hexdigest()[:12]

        # ---- 改动1: Content-Type 改为 audio/wav ----
        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'audio/wav',
                'Content-Disposition': f'attachment; filename="audio_{uid}.mp3"',
            }
        )
        await response.prepare(request)
        headers = {
            "api-key": MIMO_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "model": "mimo-v2.5-tts",
            "messages": [
                {"role": "user",      "content": cur_style},
                {"role": "assistant", "content": cleaned_text},
            ],
            "audio": {
                "format": "wav",
                "voice": voice,
            },
        }

        resp = requests.post(
            MIMO_API_URL, headers=headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        result = resp.json()
        audio_b64 = result["choices"][0]["message"]["audio"]["data"]
        audio_bytes = base64.b64decode(audio_b64)
        await response.write(audio_bytes)  # 每个 chunk 只写自己
        await response.write_eof()
        return response

    except Exception as e:
        print("异常", str(e))
        return web.json_response({"error": str(e)}, status=500)



def generate_wav(stream):
    pcm_chunks = []
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if not getattr(delta, "audio", None):
            continue
        pcm_bytes = base64.b64decode(delta.audio["data"])
        pcm_chunks.append(pcm_bytes)

    if not pcm_chunks:
        return

     # ── 拼接 PCM + 加 WAV 头 ─────────────────────────────────
    pcm_data = b"".join(pcm_chunks)
    sample_rate  = 24000
    channels     = 1
    bits         = 16
    data_size    = len(pcm_data)
    byte_rate    = sample_rate * channels * bits // 8
    block_align  = channels * bits // 8
    wav_header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,
        b'WAVE',
        b'fmt ',
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits,
        b'data',
        data_size,
    )

    wav_data = wav_header + pcm_data

    return wav_data


async def generate_mimostream(request):
    try:
        form = await request.post()
        text = form.get('text', '')
        voice = form.get('voice', 'Chloe')
        rate = form.get('rate', '0')
        style = form.get("style", "自然、口语化的对话语调")

        cleaned_text = remove_special_characters(text)
        try:
            rate_value = max(0, min(100, int(rate)))
        except ValueError:
            rate_value = 25

        diff = rate_value - 25
        if diff <= -15:
            pace = "非常慢的语速"
        elif diff <= -5:
            pace = "偏慢的语速"
        elif diff >= 15:
            pace = "非常快的语速"
        elif diff >= 5:
            pace = "偏快的语速"
        else:
            pace = "正常语速"
        cur_style = f"{style}，{pace}"


        uid = hashlib.md5(cleaned_text.encode("utf-8")).hexdigest()[:12]

        # ---- 改动1: Content-Type 改为 audio/wav ----
        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'audio/wav',
                'Content-Disposition': f'attachment; filename="audio_{uid}.mp3"',
            }
        )
        await response.prepare(request)
        client = OpenAI(
            api_key=MIMO_API_KEY,
            base_url=MIMO_OPEN_URL,
        )
        stream = client.chat.completions.create(
            model="mimo-v2.5-tts",
            messages=[
                {
                    "role": "user",
                    "content": cur_style,
                },
                {
                    "role": "assistant",
                    "content": cleaned_text,
                },
            ],
            audio={"format": "pcm16", "voice": voice},
            stream=True,
        )
        # 收集所有 PCM 块
        
        await response.write(generate_wav(stream))  # 每个 chunk 只写自己
        await response.write_eof()
        return response

    except Exception as e:
        print("异常", e)
        return web.json_response({"error": str(e)}, status=500)


app = web.Application()
app.router.add_post('/api/rap', generate_audio)
app.router.add_post('/api/mimo', generate_mimoaudio)
app.router.add_post('/api/mimostream', generate_mimostream)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=1233)