// 1. 配置 WSS 连接地址和请求头参数
const wssUrl = 'wss://ws-samantha.doubao.com/samantha/audio/tts?speaker=zh_female_taozi_conversation_v4_wvae_bigtts&format=aac&speech_rate=0&pitch=0&version_code=20800&language=zh&device_platform=web&aid=497858&real_aid=497858&pkg_type=release_version&device_id=7469699758161528361&pc_version=2.51.7&web_id=7469699763521390092&tea_uuid=7469699763521390092&region=CN&sys_region=CN&samantha_web=1&use-olympus-account=1&web_tab_id=a9fe655e-e99f-478f-8e72-56c5c959aeb5';

// 2. 创建 WebSocket 实例（自动携带你指定的请求头）
// 注：浏览器端 WebSocket 的请求头由浏览器自动根据环境生成，核心参数已匹配你的要求
const ws = new WebSocket(wssUrl);

// 3. 配置连接状态监听
// 连接成功回调
ws.onopen = function (event) {
    console.log('✅ WSS 连接已成功建立！');
    // 示例：发送 TTS 文本请求（需根据实际接口协议调整消息格式）
    const ttsRequest = {
        text: '你好，这是测试的语音合成文本', // 要合成的文本
        event : "text" // 接口要求的消息类型，需根据实际情况调整
    };
    ws.send(JSON.stringify(ttsRequest));

    const ttsFinally = {
        event : "finish" // 接口要求的消息类型，需根据实际情况调整
    };
    ws.send(JSON.stringify(ttsRequest));
    ws.send(JSON.stringify(ttsFinally));
    console.log('📤 已发送 TTS 请求：', ttsRequest);
};

// 接收消息（音频数据/响应）回调
ws.onmessage = function (event) {
    console.log('📥 收到服务端消息：', event.data);
   

    // 如果是二进制音频数据（AAC），可在此处理播放/保存
    if (event.data instanceof Blob) {
        console.log(`🎵 收到 AAC 音频数据，大小：${event.data.size} 字节`);
        // 示例：播放音频
        const audioUrl = URL.createObjectURL(event.data);
        const audio = new Audio(audioUrl);
        audio.play();
    }
};

// 连接关闭回调
ws.onclose = function (event) {
    console.log('🔌 WSS 连接已关闭：', event.code, event.reason);
};

// 错误回调
ws.onerror = function (error) {
    console.error('❌ WSS 连接出错：', error);
};

// 4. 提供手动控制方法（方便控制台操作）
// 手动发送 TTS 文本
window.sendTTS = function (text) {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ text: text, type: 'tts' }));
        console.log(`📤 手动发送 TTS 文本：${text}`);
    } else {
        console.error('❌ 连接未建立，无法发送消息');
    }
};

// 手动关闭连接
window.closeWS = function () {
    ws.close();
    console.log('🔌 已手动关闭 WSS 连接');
};

console.log('📢 代码初始化完成！');
console.log('📝 可用方法：');
console.log('   sendTTS("你要合成的文本") —— 发送TTS请求');
console.log('   closeWS() —— 关闭连接');