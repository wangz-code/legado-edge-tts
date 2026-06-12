# legado-edge-tts

edge 大声朗读微软 TTS 服务, 在阅读 APP 中添加配置语音引擎方式收听微软 TTS / Edge 大声朗读 也可以在浏览器直接访问自动下载的.mp3 文件流

## 其他说明
    - EdgeSpeakFetch.kt 是基于[edge-tts](https://github.com/rany2/edge-tts) 通过gpt提取核心逻辑生成的, 可直接在阅读内部集成
    - 理论上和rany2/edge-tts 参数都一致, 一荣俱荣一损俱损 EdgeVersion=140.0.3485.14
    - 如果没有VPS部署可以使用 https://github.com/wangz-code/legado-tts 阅读内部集成了Edge大声朗读和豆包


## 方式一 直接运行,需要 python 环境

```sh
# 如果发现接口不能使用 把 edgetts请升级到最新版: pip install -U edge-tts
pip install aiohttp edge-tts requests openai
python main.py

# 在阅读内语速最好设置为2.5     >2.5 就读的快， < 2.5 就读的慢
# 阅读内朗读引擎配置url
http://127.0.0.1:1233/api/rap,{"method": "POST", "body": "text={{encodeURIComponent(speakText)}}&rate={{speakSpeed}}&voice=zh-CN-XiaoxiaoNeural"}
```
## 增加小米 MimoTTS, 还有几天可以白嫖,后续就要收费了 导入方式同Edge,参数相同,voice 和 style 略有不同

```sh
# 需要自己注册api-key 填写在开头
http://127.0.0.1:1233/api/mimo,{"method": "POST", "body": "text={{encodeURIComponent(speakText)}}&rate={{speakSpeed}}&voice=Chloe&style=一位年迈的老先生，说带北方口音的普通话，语速缓慢而沉稳，嗓音略带沙哑和沧桑感"}
# 流式响应
http://127.0.0.1:1233/api/mimostream,{"method": "POST", "body": "text={{encodeURIComponent(speakText)}}&rate={{speakSpeed}}&voice=苏打&style=一本正经地, 压低嗓音像在密谋"}

# curl 测试
curl -X POST http://localhost:1233/api/mimo \
  -F "text=这么多年过去了，再走过那条街，心里一下子空了一块。！" \
  -F "voice=Chloe" \
  -F "style=一位年迈的老先生，说带北方口音的普通话，语速缓慢而沉稳，嗓音略带沙哑和沧桑感" \
  -F "rate=30" \
  --output result.wav
```

| 音色名 | Voice ID | 语言 | 性别 |
|--------|----------|------|------|
| MiMo-默认 | mimo_default | 因部署集群而异，中国集群默认为冰糖，其他集群默认为Mia | — |
| 冰糖 | 冰糖 | 中文 | 女性 |
| 茉莉 | 茉莉 | 中文 | 女性 |
| 苏打 | 苏打 | 中文 | 男性 |
| 白桦 | 白桦 | 中文 | 男性 |
| Mia | Mia | 英文 | 女性 |
| Chloe | Chloe | 英文 | 女性 |
| Milo | Milo | 英文 | 男性 |
| Dean | Dean | 英文 | 男性 |



## APP添加朗读引擎  📢注意点击页面的"+"号添加 祝大家玩的开心!
![detail.png](https://raw.githubusercontent.com/wangz-code/legado-edge-tts/main/demo.gif)





## /rap + /ra 其他可选参数

| 参数  | 默认值               |
| ----- | -------------------- |
| voice | zh-CN-XiaoxiaoNeural |

## 常用音色 
| 语音模型 | 性别 | 适用场景 | 风格特点 |
| --- | --- | --- | --- |
| zh-CN-XiaoxiaoNeural | Female | 新闻、小说 | 温和 |
| zh-CN-XiaoyiNeural | Female | 动漫、小说 | 活泼 |
| zh-CN-YunjianNeural | Male | 体育、小说 | 激昂 |
| zh-CN-YunxiNeural | Male | 小说 | 活泼、阳光 |
| zh-CN-YunxiaNeural | Male | 动漫、小说 | 可爱 |
| zh-CN-YunyangNeural | Male | 新闻 | 专业、可靠 |
| zh-CN-liaoning-XiaobeiNeural | Female | 方言 | 幽默 |
| zh-CN-shaanxi-XiaoniNeural | Female | 方言 | 明快 |

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


curl -X POST http://localhost:1233/api/rapmimo \
  -F "text=老板，你猜怎么着？我通过了！" \
  -F "voice=Chloe" \
  -F "style=明亮、活泼、略带欢快的语调" \
  -F "rate=30" \
  --output result.wav

# 基于
https://github.com/rany2/edge-tts

https://github.com/callmerio/doubao-tts
