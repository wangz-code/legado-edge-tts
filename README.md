# legado-edge-tts
edge大声朗读微软TTS服务, 在阅读APP中导入语音引擎方式收听微软TTS / Edge大声朗读 也可以在浏览器直接访问自动下载的.mp3 文件流


# 部署 python环境
```bash
pip install Flask edge-tts

python3 main.py


# `GET接口是 /ra  和 POST接口 /rap
# 浏览器访问: 
http://127.0.0.1:1233/api/ra?text=hello&rate=25

# 阅读导入URL: 
http://127.0.0.1:1233/api/rap,{"method": "POST", "body": "text={{encodeURI(speakText)}}&rate={{speakSpeed}}"}

# 在阅读内开启 "流式播放音频" 更好
# 语速最好设置为2.5     >2.5 就读的快， < 2.5 就读的慢
```

# 基于
https://github.com/rany2/edge-tts