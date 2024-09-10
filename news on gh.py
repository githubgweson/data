import time
import requests
import pandas as pd
import json
import os

class CnyesNewsSpider():
    
    def get_newslist_info(self, page=1, limit=50):
        """
        從鉅亨網新聞 API 獲取新聞列表

        :param page: 頁數
        :param limit: 一頁新聞數量
        :return newslist_info: 新聞資料
        """
        headers = {
            'Origin': 'https://news.cnyes.com/',
            'Referer': 'https://news.cnyes.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
        r = requests.get(f"https://api.cnyes.com/media/api/v1/newslist/category/headline?page={page}&limit={limit}", headers=headers)
        if r.status_code != requests.codes.ok:
            print('請求失敗', r.status_code)
            return None
        newslist_info = r.json()['items']
        return newslist_info

    def process_news(self, newslist_info, start=0, top_n=10):
        """
        處理並格式化新聞資料，返回新聞的表格
        :param newslist_info: 從 API 獲得的新聞資料
        :param start: 起始新聞索引
        :param top_n: 需要列出的新聞數量
        :return: 以 DataFrame 格式返回的新聞表格
        """
        processed_news = []

        # 只處理從 start 到 start + top_n 條新聞
        for i, news in enumerate(newslist_info["data"][start:start+top_n], start=start+1):
            news_id = news["newsId"]
            url = f'https://news.cnyes.com/news/id/{news_id}'
            title = news["title"]  # 標題不壓縮，完整顯示
            summary = news["summary"] if news["summary"] is not None else "無摘要"
            pub_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(news["publishAt"]))
            keywords = news.get("keyword", [])
            keywords_str = ", ".join(keywords) if keywords else "無關鍵字"
            category = f'{news["categoryName"]} (id:{news["categoryId"]})'

            # 將每條新聞的資料格式化
            processed_news.append({
                '序號': i,  # 添加序號
                '標題': f'<a href="{url}" target="_blank">{title}</a> <br> {pub_time}',  # 讓連結在新分頁打開
                '概要': f"{summary} <br> {url} <br>",
                '關鍵字': f"{keywords_str} <br> {category}"
            })

        # 將新聞列表轉換為 DataFrame
        df = pd.DataFrame(processed_news)
        return df

    def generate_html(self, top10_df, df_11_30, df_31_50, active_section=1, output_file="news_top10.html"):
        """
        生成不同狀態的 HTML，根據 active_section 參數控制按鈕的狀態。
        :param top10_df: 前10條新聞的 DataFrame
        :param df_11_30: 第11-30條新聞的 DataFrame
        :param df_31_50: 第31-50條新聞的 DataFrame
        :param active_section: 當前激活的新聞部分 (1, 2, or 3)
        :param output_file: 輸出的 HTML 檔名
        """
        top10_html = top10_df.to_html(escape=False, index=False)  # 移除索引欄位
        df_11_30_html = df_11_30.to_html(escape=False, index=False)
        df_31_50_html = df_31_50.to_html(escape=False, index=False)

        # 根據 active_section 控制按鈕樣式
        button_style_1 = "background-color: lightblue;" if active_section == 1 else ""
        button_style_2 = "background-color: lightblue;" if active_section == 2 else ""
        button_style_3 = "background-color: lightblue;" if active_section == 3 else ""

        section_html_1 = top10_html if active_section == 1 else ""
        section_html_2 = df_11_30_html if active_section == 2 else ""
        section_html_3 = df_31_50_html if active_section == 3 else ""

        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body>
            <button style="{button_style_1}" onclick="window.location.href='news_top10.html'">第 1-10 條即時新聞</button>
            <button style="{button_style_2}" onclick="window.location.href='news_11_30.html'">第 11-30 條即時新聞</button>
            <button style="{button_style_3}" onclick="window.location.href='news_31_50.html'">第 31-50 條即時新聞</button>
            <div>{section_html_1}</div>
            <div>{section_html_2}</div>
            <div>{section_html_3}</div>
        </body>
        </html>
        """

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

def save_news_to_json(newslist_info, output_file="news.json"):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(newslist_info, f, ensure_ascii=False, indent=4)

def generate_html_files(spider, output_dir="news_html"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    newslist_info = spider.get_newslist_info()
    save_news_to_json(newslist_info)  # 保存為 JSON 檔案

    top10_df = spider.process_news(newslist_info, start=0, top_n=10)
    df_11_30 = spider.process_news(newslist_info, start=10, top_n=20)
    df_31_50 = spider.process_news(newslist_info, start=30, top_n=20)

    spider.generate_html(top10_df, df_11_30, df_31_50, active_section=1, output_file=os.path.join(output_dir, "news_top10.html"))
    spider.generate_html(top10_df, df_11_30, df_31_50, active_section=2, output_file=os.path.join(output_dir, "news_11_30.html"))
    spider.generate_html(top10_df, df_11_30, df_31_50, active_section=3, output_file=os.path.join(output_dir, "news_31_50.html"))

# 使用範例
spider = CnyesNewsSpider()
generate_html_files(spider)
