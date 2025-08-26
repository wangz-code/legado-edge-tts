# legado-edge-tts

edge 大声朗读微软 TTS 服务, 在阅读 APP 中添加配置语音引擎方式收听微软 TTS / Edge 大声朗读 也可以在浏览器直接访问自动下载的.mp3 文件流

## 其他说明
    - min.py 是精简版 仅有一个接口'
    - golang-tts 是基于rany2/edge-tts 通过gpt提取核心逻辑生成的  app编译成二进制.so 文件,通过 jni 加载 作为内置tts使用
    - java-tts 是基于rany2/edge-tts 通过gpt提取核心逻辑生成的, 可以直接集成
    - 你也可以使用 golang api 部署在自己的vps上, 或许内存占用会低一点,效率会高一点
    - 理论上和rany2/edge-tts 参数都一致, 一荣俱荣一损俱损

## 如果没有VPS可以使用 [https://github.com/wangz-code/legado](https://github.com/wangz-code/legado-with-edgetts)  这个阅读内部集成了Edge大声朗读
 - 修改音频流的暂存方式 (写硬盘=>写内存)
 原来是把音频缓存硬盘上会频繁执行写入和删除(有多少段落就写多少次),  我不确定频繁执行写入会不会影响寿命或许对于现代存储来说影响微乎其微😋
 `我改成了放在内存中`, 每读完一章就释放已读完的的媒体, 修改内容参见:https://github.com/gedoor/legado/pull/5304

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
# 运行,负载均衡, 进程守护：PM2 可以始终保持应用程序运行。当应用程序崩溃时，PM2 可以自动重启它，确保服务的可用性。
pm2 start "python3 main.py"
```

# 基于

https://github.com/rany2/edge-tts
