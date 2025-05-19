# legado-edge-tts

edge 大声朗读微软 TTS 服务, 在阅读 APP 中添加配置语音引擎方式收听微软 TTS / Edge 大声朗读 也可以在浏览器直接访问自动下载的.mp3 文件流

## 新增Fish Speech TTS  
体验 地址 http://wz.djgo.cc:2334 仅白天随机开机,晚上会关机睡觉太吵, 初步感觉比不过edge但是克隆音色很有意思, 随便一两句话就能对应的音色

## 方式一 直接运行,需要 python 环境

```sh
pip3 install Flask edge-tts

python3 main.py


# `GET接口是 /ra  和 POST接口 /rap
# 浏览器访问:
http://127.0.0.1:1233/api/ra?text=hello&rate=25

# 阅读内朗读引擎配置url
http://127.0.0.1:1233/api/rap,{"method": "POST", "body": "text={{encodeURIComponent(speakText)}}&rate={{speakSpeed}}"}

# 阅读内朗读引擎配置url 支持对话&旁白切换音色   感谢 https://github.com/retaw106 贡献
http://127.0.0.1:1233/api/rap2,{"method": "POST", "body": "text={{encodeURIComponent(speakText)}}&rate={{speakSpeed}}"}

# 在阅读内开启 "流式播放音频" 更好
# 语速最好设置为2.5     >2.5 就读的快， < 2.5 就读的慢
```


## APP添加朗读引擎  📢注意点击页面的"+"号添加 祝大家玩的开心!
![detail.png](https://raw.githubusercontent.com/wangz-code/legado-edge-tts/main/demo.gif)


## /rap + /ra 其他可选参数

| 参数  | 默认值               |
| ----- | -------------------- |
| voice | zh-CN-XiaoxiaoNeural |

## /rap2 其他可选参数

| 参数        | 默认值               | 描述     |
| ----------- | -------------------- | -------- |
| voice       | zh-CN-XiaoxiaoNeural | 旁白音色 |
| voice_chat  | zh-CN-YunxiNeural    | 对话音色 |
| volume_chat | 0                    | 对话音量 |

## 方式二 使用 pm2 运行, 需要 node 环境

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
