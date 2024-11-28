#!/usr/bin/env python3

from flask import Flask, send_file, request, Response
import edge_tts
import io

app = Flask(__name__)


@app.route("/api/ra", methods=["GET"])
def generate_audio():
    # 从查询参数中获取 text 和 voice
    text = request.args.get("text", default="说点什么吧", type=str)
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
    text = request.form.get("text", default="")
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1233)
