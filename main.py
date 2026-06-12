#!/usr/bin/env python3

from flask import Flask, send_file, request, Response
import edge_tts
import io
import re
from urllib.parse import unquote
import base64
import os
import requests
MIMO_API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "替换这个字符串里为你的api-key sk-xxxx")
app = Flask(__name__)


def remove_special_characters(text):
    text = unquote(text)
    # 定义正则表达式，保留字母、数字、中文、空格和常见的标点符号
    pattern = r'[^\w\s\u4e00-\u9fff，。！？；：、（）《》【】“”‘’]'
    # 使用正则表达式替换特殊符号为空字符串
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text


@app.route("/api/ra", methods=["GET"])
def generate_audio():
    # 从查询参数中获取 text 和 voice
    text = remove_special_characters(request.args.get("text", default="说点什么吧", type=str))
    voice = request.args.get("voice", default="zh-CN-XiaoxiaoNeural", type=str)
    rate = request.args.get("rate", default="0")  # 默认值为 0%
    centerRate = 25  # 阅读的语速中间值
    try:
        rate_value = int(rate)  # 尝试将 rate 转换为整数
    except ValueError:
        rate_value = 0  # 如果转换失败，则将 rate 设置为 0

    if rate_value < centerRate:
        custom_rate = "-" + str((centerRate - rate_value)) + "%"  # 低于 50%
    else:
        custom_rate = "+" + str((rate_value - centerRate)) + "%"  # 高于 50%
    # 使用 edge_tts 生成音频
    communicate = edge_tts.Communicate(text, voice, rate=custom_rate)

    audio_stream = io.BytesIO()

    for chunk in communicate.stream_sync():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])

    audio_stream.seek(0)  # Reset the stream to the beginning

    return send_file(
        audio_stream,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name="audio.mp3",
    )


@app.route("/api/rap", methods=["POST"])
def generate_audiop():
    # 从表单数据中获取 text 和 voice
    text = remove_special_characters(request.form.get("text", default=""))
    voice = request.form.get("voice", default="zh-CN-XiaoxiaoNeural")
    rate = request.form.get("rate", default="0")  # 默认值为 0%
    centerRate = 25  # 阅读的语速中间值
    try:
        rate_value = int(rate)  # 尝试将 rate 转换为整数
    except ValueError:
        rate_value = 0  # 如果转换失败，则将 rate 设置为 0

    if rate_value < centerRate:
        custom_rate = "-" + str((centerRate - rate_value)) + "%"  # 低于 50%
    else:
        custom_rate = "+" + str((rate_value - centerRate)) + "%"  # 高于 50%

    # 使用 edge_tts 生成音频
    communicate = edge_tts.Communicate(text, voice, rate=custom_rate)
    audio_stream = io.BytesIO()

    for chunk in communicate.stream_sync():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])

    audio_stream.seek(0)  # Reset the stream to the beginning

    return send_file(
        audio_stream,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name="audio.mp3",
    )




def split_chat(text):
    # 使用正则表达式匹配对话部分
    dialogue_pattern = dialogue_pattern = r'“([^”]*[。！？，；])”'
    dialogues = re.finditer(dialogue_pattern, text)

    if not dialogues:
        return [[dialogues, 0]]

    # 初始化结果列表
    result = []

    # 上一个对话结束的位置
    last_end = 0

    # 遍历每个对话
    for match in dialogues:
        # 获取对话前的旁白
        pre_dialogue_text = text[last_end:match.start()].strip()
        if pre_dialogue_text:
            result.append([pre_dialogue_text, 0])
        
        # 获取对话内容
        dialogue_text = match.group(0).strip()
        if dialogue_text:
            result.append([dialogue_text, 1])
        
        # 更新最后一个对话结束的位置
        last_end = match.end()

    # 获取最后一个对话后的旁白
    post_dialogue_text = text[last_end:].strip()
    if post_dialogue_text:
        result.append([post_dialogue_text, 0])

    return result


@app.route("/api/rap2", methods=["POST"])
def generate_audiop2():
    # 从表单数据中获取 text 和 voice
    text = remove_special_characters(request.form.get("text", default=""))
    voice = request.form.get("voice", default="zh-CN-XiaoxiaoNeural")  # 旁白
    voice_chat = request.form.get("voice_chat", default="zh-CN-YunxiNeural")  # 对话
    volume_chat = request.form.get("volume_chat", default="0")  # 对话的音量调整
    rate = request.form.get("rate", default="0")  # 默认值为 0%
    centerRate = 25  # 阅读的语速中间值
    try:
        rate_value = int(rate)  # 尝试将 rate 转换为整数
    except ValueError:
        rate_value = 0  # 如果转换失败，则将 rate 设置为 0

    if rate_value < centerRate:
        custom_rate = "-" + str((centerRate - rate_value)) + "%"  # 低于 50%
    else:
        custom_rate = "+" + str((rate_value - centerRate)) + "%"  # 高于 50%
    
    try:
        volume_chat = int(volume_chat)  # 尝试将 volume_chat 转换为整数
    except ValueError:
        volume_chat = 0  # 如果转换失败，则将 volume_chat 设置为 0
    volume_chat = "+" + str(volume_chat) + "%"

    # 使用 edge_tts 生成音频
    audio_stream = io.BytesIO()

    text_splitted = split_chat(text)
    for text_seg in text_splitted:
        if text_seg[1] == 0:
            communicate = edge_tts.Communicate(text_seg[0], voice, rate=custom_rate)
        else:
            communicate = edge_tts.Communicate(text_seg[0], voice_chat, rate=custom_rate, volume=volume_chat)
        for chunk in communicate.stream_sync():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])

    audio_stream.seek(0)  # Reset the stream to the beginning

    return send_file(
        audio_stream,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name="audio.mp3",
    )



def _mimo_tts(text: str, voice: str, style: str) -> bytes:
    """调用 MiMo TTS 接口，返回 wav 音频字节"""

    print("MIMO_API_KEY",MIMO_API_KEY)
    headers = {
        "api-key": MIMO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mimo-v2.5-tts",
        "messages": [
            {"role": "user", "content": style},
            {"role": "assistant", "content": text},
        ],
        "audio": {
            "format": "wav",
            "voice": voice,
        },
    }
    resp = requests.post(MIMO_API_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    result = resp.json()
    audio_b64 = result["choices"][0]["message"]["audio"]["data"]
    return base64.b64decode(audio_b64)


@app.route("/api/rapmimo", methods=["POST"])
def generate_audio_mimo():
    # ── 参数读取 ──────────────────────────────────────────────
    text = remove_special_characters(request.form.get("text", default=""))
    voice = request.form.get("voice", default="Chloe")
    style = request.form.get("style", default="自然、口语化的对话语调")
    rate = request.form.get("rate", default="25")

    # ── 语速映射 ──────────────────────────────────────────────
    center_rate = 25
    try:
        rate_value = int(rate)
    except ValueError:
        rate_value = center_rate

    diff = rate_value - center_rate
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

    # ── 拆分文本，逐段合成 ────────────────────────────────────
    text_splitted = split_chat(text)
    audio_stream = io.BytesIO()

    for seg_text, _seg_type in text_splitted:
        if not seg_text.strip():
            continue

        try:
            audio_bytes = _mimo_tts(seg_text, voice, cur_style)
            audio_stream.write(audio_bytes)
        except requests.RequestException as e:
            return {"error": f"MiMo TTS 调用失败: {str(e)}"}, 502
        except (KeyError, IndexError) as e:
            return {"error": f"MiMo 返回格式异常: {str(e)}"}, 500

    audio_stream.seek(0)

    return send_file(
        audio_stream,
        mimetype="audio/wav",
        as_attachment=True,
        download_name="audio.wav",
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1233)
