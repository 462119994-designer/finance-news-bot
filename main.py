import os, requests, feedparser
from datetime import datetime, timezone

SC_KEY = os.environ.get('SC_KEY')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
_UA = {"User-Agent": "Mozilla/5.0"}

def grab():
    srcs = [
      ("市场", f"https://news.google.com/rss/search?q=A股+OR+港股+OR+美股&hl=zh-CN&gl=HK&ceid=HK:zh-Hant"),
      ("宏观", f"https://news.google.com/rss/search?q=美联储+OR+降息+OR+央行&hl=zh-CN&gl=US&ceid=US:en"),
      ("公司", f"https://news.google.com/rss/search?q=NVIDIA+OR+AI芯片+OR+科技公司&hl=en&gl=US&ceid=US:en"),
    ]
    out=[]
    for tag,(url,) in [(t,(u,)) for t,u in srcs]:
        u=url
        try:
            f=feedparser.parse(requests.get(u,headers=_UA,timeout=10).content)
            for e in f.entries[:6]:
                t2=(e.get("title") or "").strip()
                l=(e.get("link")or"").strip()
                s=(e.get("summary")or"").strip()[:120]
                if t2: out.append(f"【{tag}】{t2}\n{l}\n{s}")
        except: pass
    return "\n\n---\n\n".join(out[:20])

def ai_sum(raw):
    if not (DEEPSEEK_API_KEY or "").startswith("sk-"):
        return raw
    try:
        r=requests.post("https://api.deepseek.com/chat/completions",
            headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"},
            json={"model":"deepseek-chat","messages":[{"role":"user","content":
                "你是财经编辑，把下方原始新闻整理成Markdown早报，分## 📊 市场行情 / ## 🏛️ 宏观政策 / ## 🏢 公司动态，每条- **标题**：≤50字，末行加> ⚠️ 不构成投资建议。\n"+raw
            }],"temperature":0.3},timeout=60)
        return r.json()["choices"][0]["message"]["content"]
    except: return raw

def push(md):
    r=requests.post(f"https://sctapi.ftqq.com/{SC_KEY}.send",
        data={"title":f"📈 早报 | {datetime.now():%m-%d}","desp":md},timeout=15)
    print(r.text)

if __name__=="__main__":
    raw=grab()
    push(ai_sum(raw) if (DEEPSEEK_API_KEY or "").startswith("sk-") else raw)
