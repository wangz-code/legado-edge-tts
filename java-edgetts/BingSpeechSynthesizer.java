package xyz;

import okio.ByteString;
import okhttp3.*;
import java.io.FileOutputStream;
import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.CountDownLatch;

public class BingSpeechSynthesizer {
    // 常量定义（与Golang完全一致）
    private static final String TrustedClientToken = "6A5AA1D4EAFF4E9FB37E23D68491D6F4";
    private static final String BaseURL = "speech.platform.bing.com";
    private static final String WSSPath = "/consumer/speech/synthesize/readaloud/edge/v1";
    private static final String SecMsGecVersion = "1-130.0.2849.68";
    private static final String DefaultVoice = "zh-CN-XiaoxiaoNeural";

    // DRM 相关参数（与Golang完全一致）
    private static final long WIN_EPOCH_SECONDS = 11644473600L;
    private static final double S_TO_NS = 1e9;

    private FileOutputStream audioFile;
    private boolean audioReceived = false;
    private final CountDownLatch latch = new CountDownLatch(1);

    public static void main(String[] args) {
        try {
            new BingSpeechSynthesizer().run();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void run() throws Exception {
        // 时钟偏移（与Golang一致）
        double clockSkewSeconds = 0.0;

        // 生成Sec-MS-GEC token（核心逻辑与Golang一致）
        String secMsGec = generateSecMsGec(clockSkewSeconds);
        System.out.println("Sec-MS-GEC Token: " + secMsGec);

        // 生成ConnectionId（与Golang一致：无破折号UUID）
        String connectionId = connectID();

        // 调整参数顺序为：ConnectionId -> Sec-MS-GEC -> Sec-MS-GEC-Version -> TrustedClientToken
        String queryParams = String.format(
                "ConnectionId=%s&Sec-MS-GEC=%s&Sec-MS-GEC-Version=%s&TrustedClientToken=%s",
                connectionId,
                secMsGec,
                SecMsGecVersion,
                TrustedClientToken
        );

        String wsUrl = String.format("wss://%s%s?%s", BaseURL, WSSPath, queryParams);
        System.out.println("Connecting to: " + wsUrl);

        // 准备音频文件输出（与Golang一致：output.mp3）
        FileOutputStream audioFile = new FileOutputStream("output.mp3");

        // 倒计时锁（用于阻塞主线程）
        CountDownLatch latch = new CountDownLatch(1);

        // 配置OkHttp客户端
        OkHttpClient client = new OkHttpClient.Builder()
                .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                .build();

        // 创建WebSocket请求
        Request request = new Request.Builder().url(wsUrl).build();

        // 建立WebSocket连接
        WebSocket webSocket = client.newWebSocket(request, new WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                System.out.println("WebSocket连接已建立");
                try {
                    // 发送speech.config消息（格式与Golang完全一致）
                    sendSpeechConfig(webSocket);

                    // 构造并发送SSML消息
                    String text = "但这里数值很大，用long可能溢出？所以用BigDecimal或double";
                    String ssml = mkSSML(text, DefaultVoice, "+0Hz", "+0%", "+0%");
                    sendSSMLMessage(webSocket, ssml);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }

            @Override
            public void onMessage(WebSocket webSocket, String text) {
                System.out.println("Text message: " + text);
                // 检测turn.end并关闭连接（与Golang逻辑一致）
                if (text.contains("turn.end")) {
                    System.out.println("发现 END break 结束 Close");
                    webSocket.close(1000, "正常结束");
                    try {
                        audioFile.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    latch.countDown();
                } else {
                    System.out.println("继续");
                }
            }

            @Override
            public void onMessage(WebSocket webSocket, ByteString bytes) {
                try {
                    // 处理二进制音频数据（与Golang解析逻辑一致）
                    byte[] message = bytes.toByteArray();
                    if (message.length < 2) {
                        System.out.println("binary message too short");
                        return;
                    }

                    // 解析头部长度（前2字节big endian，与Golang一致）
                    int headerLength = ((message[0] & 0xFF) << 8) | (message[1] & 0xFF);
                    if (headerLength > message.length) {
                        System.out.println("invalid header length");
                        return;
                    }

                    // 提取音频数据（跳过头部，与Golang一致）
                    byte[] audioData = new byte[message.length - headerLength - 2];
                    System.arraycopy(message, headerLength + 2, audioData, 0, audioData.length);

                    if (audioData.length > 0) {
                        audioFile.write(audioData);
                        audioReceived = true;
                    } else {
                        System.out.println("empty audio data");
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }

            @Override
            public void onFailure(WebSocket webSocket, Throwable t, Response response) {
                System.err.println("连接失败: " + t.getMessage());
                t.printStackTrace();
                try {
                    audioFile.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
                latch.countDown();
            }

            @Override
            public void onClosed(WebSocket webSocket, int code, String reason) {
                System.out.println("WebSocket已关闭: " + reason);
                latch.countDown();
            }
        });

        // 阻塞等待完成
        latch.await();
        webSocket.cancel();
    }

    public static String generateSecMsGec(double clockSkewSeconds) {
        // 获取当前UTC时间戳（秒）
        double now = Instant.now().getEpochSecond() + clockSkewSeconds;

        // 转换为Windows文件时间（从1601-01-01开始的秒数）
        double ticks = now + WIN_EPOCH_SECONDS;

        // 向下取整到最近的5分钟（300秒）
        ticks = ticks - (long)ticks % 300;

        // 转换为100纳秒单位
        ticks = ticks * (S_TO_NS / 100);

        // 拼接待哈希字符串
        String strToHash = String.format("%.0f%s", ticks, TrustedClientToken);

        // 计算SHA-256哈希
        return sha256(strToHash);
    }

    private static String sha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes());
            return bytesToHex(hash).toUpperCase();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 algorithm not available", e);
        }
    }

    private static String bytesToHex(byte[] bytes) {
        return HexFormat.of().formatHex(bytes);
    }

    // 构造SSML文本（与Golang格式完全一致）
    private String mkSSML(String text, String voice, String pitch, String rate, String volume) {
        return String.format(
                "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>" +
                        "<voice name='%s'>" +
                        "<prosody pitch='%s' rate='%s' volume='%s'>%s</prosody>" +
                        "</voice>" +
                        "</speak>",
                voice, pitch, rate, volume, text
        );
    }

    // 发送speech.config消息（格式与Golang完全一致）
    private void sendSpeechConfig(WebSocket webSocket) throws IOException {
        String speechConfig = "{\"context\":{\"synthesis\":{\"audio\":{\"metadataoptions\":{\"sentenceBoundaryEnabled\":\"false\",\"wordBoundaryEnabled\":\"true\"},\"outputFormat\":\"audio-24khz-48kbitrate-mono-mp3\"}}}}";

        // 时间格式严格匹配Golang的time.RFC1123
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss z", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("UTC"));
        String timestamp = sdf.format(new Date());

        String speechConfigMsg = String.format(
                "X-Timestamp:%s\r\nContent-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n%s\r\n",
                timestamp, speechConfig
        );
        webSocket.send(speechConfigMsg);
    }

    // 发送SSML消息（格式与Golang完全一致）
    private void sendSSMLMessage(WebSocket webSocket, String ssml) throws IOException {
        String requestId = connectID();
        // 时间格式严格匹配Golang的"Mon Jan 2 2006 15:04:05 GMT-0700 (MST)"
        SimpleDateFormat sdf = new SimpleDateFormat("EEE MMM d yyyy HH:mm:ss zzz", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("UTC"));
        String timestamp = sdf.format(new Date());

        String ssmlMsg = String.format(
                "X-RequestId:%s\r\nContent-Type:application/ssml+xml\r\nX-Timestamp:%sZ\r\nPath:ssml\r\n\r\n%s",
                requestId, timestamp, ssml
        );
        webSocket.send(ssmlMsg);
    }

    // 生成无破折号的UUID（与Golang一致）
    private String connectID() {
        return UUID.randomUUID().toString().replaceAll("-", "");
    }


}