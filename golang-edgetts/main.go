package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"log"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
)

// 常量定义
const (
	TrustedClientToken = "6A5AA1D4EAFF4E9FB37E23D68491D6F4"
	BaseURL            = "speech.platform.bing.com"
	WSSPath            = "/consumer/speech/synthesize/readaloud/edge/v1"
	SecMsGecVersion    = "1-140.0.3485.14" // 版本号示例，需同步更新
	DefaultVoice       = "zh-CN-XiaoxiaoNeural"
)

// DRM 相关参数
const (
	WinEpochSeconds = 11644473600
	SToNs           = 1e9
)

// 生成Sec-MS-GEC token，参考drm.py generate_sec_ms_gec
func generateSecMsGec(clockSkewSeconds float64) string {
	// 当前Unix时间加时钟偏移
	now := float64(time.Now().UTC().Unix()) + clockSkewSeconds

	// 转换为Windows文件时间格式（1601年起的100纳秒间隔）
	ticks := now + WinEpochSeconds

	// 向下取整到5分钟 (300秒)
	ticks = ticks - float64(int64(ticks)%300)

	// 转换为100纳秒单位
	ticks = ticks * (SToNs / 100)

	// 拼接字符串
	strToHash := fmt.Sprintf("%.0f%s", ticks, TrustedClientToken)

	// SHA256哈希
	h := sha256.Sum256([]byte(strToHash))

	return strings.ToUpper(hex.EncodeToString(h[:]))
}

// 构造SSML文本
func mkSSML(text, voice, pitch, rate, volume string) string {
	return fmt.Sprintf(
		`<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
            <voice name='%s'>
                <prosody pitch='%s' rate='%s' volume='%s'>%s</prosody>
            </voice>
        </speak>`,
		voice, pitch, rate, volume, text,
	)
}

// 发送消息格式化函数
func ssmlHeadersPlusData(requestId, timestamp, ssml string) string {
	return fmt.Sprintf(
		"X-RequestId:%s\r\nContent-Type:application/ssml+xml\r\nX-Timestamp:%sZ\r\nPath:ssml\r\n\r\n%s",
		requestId, timestamp, ssml,
	)
}

// 生成无破折号的UUID
func connectID() string {
	u := uuid.New()
	return strings.ReplaceAll(u.String(), "-", "")
}

func main() {
	// 时钟偏移，初始为0
	clockSkewSeconds := 0.0

	// 生成Sec-MS-GEC token
	secMsGec := generateSecMsGec(clockSkewSeconds)
	fmt.Println("Sec-MS-GEC Token:", secMsGec)

	// 构造WebSocket连接URL
	u := url.URL{
		Scheme: "wss",
		Host:   BaseURL,
		Path:   WSSPath,
	}
	query := url.Values{}
	query.Set("TrustedClientToken", TrustedClientToken)
	query.Set("Sec-MS-GEC", secMsGec)
	query.Set("Sec-MS-GEC-Version", SecMsGecVersion)
	query.Set("ConnectionId", connectID())
	u.RawQuery = query.Encode()

	fmt.Println("Connecting to:", u.String())

	// 建立WebSocket连接
	c, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		log.Fatal("dial:", err)
	}
	defer c.Close()

	// 发送speech.config消息
	speechConfig := `{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"true"},"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}`
	speechConfigMsg := fmt.Sprintf(
		"X-Timestamp:%s\r\nContent-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n%s\r\n",
		time.Now().UTC().Format(time.RFC1123), speechConfig,
	)
	err = c.WriteMessage(websocket.TextMessage, []byte(speechConfigMsg))
	if err != nil {
		log.Fatal("write speech.config:", err)
	}

	// 构造SSML文本
	text := "当前免费计划限制最大上下文tokens"
	ssml := mkSSML(text, DefaultVoice, "+0Hz", "+0%", "+0%")

	// 发送SSML消息
	ssmlMsg := ssmlHeadersPlusData(connectID(), time.Now().UTC().Format("Mon Jan 2 2006 15:04:05 GMT-0700 (MST)"), ssml)
	err = c.WriteMessage(websocket.TextMessage, []byte(ssmlMsg))
	if err != nil {
		log.Fatal("write ssml:", err)
	}

	// 打开文件保存音频
	audioFile, err := os.Create("output.mp3")
	if err != nil {
		log.Fatal("create file:", err)
	}
	defer audioFile.Close()

	audioReceived := false

	// 读取消息循环
	for {
		messageType, message, err := c.ReadMessage()
		if err != nil {
			log.Println("read:", err)
			break
		}

		switch messageType {
		case websocket.TextMessage:
			// 解析文本消息（元数据等），这里简单打印
			fmt.Println("Text message:", string(message))
			// 查找子字符串在主字符串中首次出现的位置
			index := strings.Index(string(message), "turn.end")
			if index != -1 {
				c.Close()
				fmt.Printf("发现 END break 结束 Close")
				break
			} else {
				fmt.Printf("继续")
			}

		case websocket.BinaryMessage:
			// 二进制消息是音频数据，写入文件
			if len(message) < 2 {
				log.Println("binary message too short")
				continue
			}

			// 头部长度为前2字节big endian
			headerLength := int(message[0])<<8 | int(message[1])
			if headerLength > len(message) {
				log.Println("invalid header length")
				continue
			}

			// 解析头部，略（可根据python代码实现）

			// 音频数据在 headerLength + 2 后
			audioData := message[headerLength+2:]

			if len(audioData) == 0 {
				log.Println("empty audio data")
				continue
			}

			// 写入文件
			_, err := audioFile.Write(audioData)
			if err != nil {
				log.Println("write audio file error:", err)
				break
			}
			audioReceived = true

		default:
			log.Println("unknown message type:", messageType)
		}
	}

	if !audioReceived {
		log.Fatal("No audio received from the service")
	}

	fmt.Println("Audio saved to output.mp3")
}
