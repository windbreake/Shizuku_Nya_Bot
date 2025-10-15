import requests
import csv


def search_and_save(query, filename="results.csv"):
    API_KEY = "sk-0f0c3eea391f468bbe7bb027a98e62f8"
    url = "https://api.bochaai.com/v1/web-search"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"query": query, "count": 10}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()["data"]["webPages"]["value"]
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["标题", "链接", "摘要"])
            for item in data:
                writer.writerow([item["name"], item["url"], item["snippet"]])
        print(f"结果已保存至{filename}！")
    else:
        print("搜索失败！")


# 使用示例
search_and_save("深度学习框架对比")
