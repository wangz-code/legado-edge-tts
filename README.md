# legado-edge-tts
edge大声朗读微软TTS服务, 在阅读APP中导入语音引擎方式收听微软TTS / Edge大声朗读 也可以在浏览器直接访问自动下载的.mp3 文件流


# 方式一 直接运行,需要python环境
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
# 方式二 使用pm2运行, 需要node环境

```bash 
# 如果没有node 需要先安装node, 推荐使用nvm  https://github.com/nvm-sh/nvm
node -v 
# 安装pm2 至全局
npm install pm2 -g
# 生成启动脚本
echo "python3 main.py" > tts.sh
# 增加运行权限
chmod a+x tts.sh
# 运行,负载均衡, 进程守护：PM2 可以始终保持应用程序运行。当应用程序崩溃时，PM2 可以自动重启它，确保服务的可用性。
pm2 start tts.sh
```

# 基于
https://github.com/rany2/edge-tts