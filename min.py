#!/usr/bin/env python3
import asyncio
from aiohttp import web
import edge_tts
import re
from urllib.parse import unquote

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

app = web.Application()
app.router.add_post('/api/rap', generate_audio)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=1233)