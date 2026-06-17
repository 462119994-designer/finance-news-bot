import os
import requests
import feedparser
from datetime import datetime

# ---------- 读取密钥 ----------
SC_KEY = os.environ.get('SC_KEY')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ---------- 抓取 RSS ----------
def fetch_news():
    print("📡 正在抓取财经新闻...")
    sources = {
        "A股/港股": "https://news.google.com/rss/search?q=A股+OR+港股+OR+上证指数+OR+恒生指数&hl=zh-CN&gl=HK&ceid=HK:zh-Hant",
        "宏观/政策": "https://news.google.com/rss/search?q=美联储+OR+降息+OR+中国央行+OR+宏观经济&hl=zh-CN&gl=US&ceid=US:en",
        "公司/科技": "https://news.google.com/rss/search?q=NVIDIA+OR+苹果+OR+AI芯片+OR+DeepSeek&hl=en&gl=US&ceid=US:en",
        "财联社": "https://www.cls.cn/api/rss"
    }
    
    news_list = []
    for category, url in sources.items():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:5]:  # 每个源取5条
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                summary = entry.get('summary', '').strip()
                if title and link:
                    # 保留摘要，方便AI提取核心信息
                    news_list.append(f"【{category}】{title}\n链接: {link}\n详情: {summary[:150]}")
        except Exception as e:
            print(f"抓取 {category} 失败: {e}")
            
    return "\n\n---\n\n".join(news_list[:20])  # 合并成文本给AI

# ---------- 调用 DeepSeek 总结 ----------
def summarize_with_deepseek(raw_news):
    print("🤖 正在调用 DeepSeek 生成简报...")
    if not DEEPSEEK_API_KEY:
        return "⚠️ 未配置 DEEPSEEK_API_KEY，无法生成摘要。"

    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 核心 Prompt：告诉 AI 你喜欢的格式
    prompt = f"""
    你是一位专业的财经编辑。请根据以下抓取到的原始新闻，整理出一份 Markdown 格式的早报。
    要求：
    1. 筛选出最重要、最有影响力的 12-15 条新闻。
    2. 分成三个板块：## 📊 市场行情、## 🏛️ 宏观政策、## 🏢 公司动态。
    3. 每条新闻格式为：
       - **标题** | 来源媒体
         一句话核心摘要（不超过50字）。
    4. 末尾加上一句免责声明：> ⚠️ 资讯仅供参考，不构成投资建议。
    5. 语言要精炼、专业，适合手机阅读。

    原始新闻数据：
    {raw_news}
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"DeepSeek API 调用失败: {e}")
        return raw_news  # 如果AI挂了，退回原始新闻

# ---------- 推送到微信 ----------
def push_to_wechat(content):
    print("📲 正在推送到微信...")
    title = f"📈 财经早报 | {datetime.now().strftime('%m-%d')}"
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    
    data = {"title": title, "desp": content}
    r = requests.post(url, data=data, timeout=15)
    print("Server酱返回:", r.text)

# ---------- 主流程 ----------
if __name__ == "__main__":
    raw_news = fetch_news()
    if not raw_news:
        push_to_wechat("⚠️ 今日抓取新闻为空，请检查 RSS 源。")
    else:
        final_report = summarize_with_deepseek(raw_news)
        push_to_wechat(final_report)
