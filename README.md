## 项目简介
* Task2 - 爬虫模块：使用网络爬虫从指定网站抓取原始文本数据。
* Task3 - 数据预处理与可视化：对采集到的数据进行清洗、分词、去噪处理，并借助可视化手段探索数据特征。
* Task4 - LDA建模：应用 Latent Dirichlet Allocation（LDA）主题模型，对文本数据进行主题挖掘和建模。
* Task6 - 情感分析：基于百度云 API 对文本进行情感分类，评估文本正负面倾向。

## 项目结构

```
Gouxionghui/
│           
├───README.md
├───requirements.txt
│           
├───code/
│   │   task3.ipynb # task3代码
│   │   task4.ipynb # task4代码
│   │   task6.ipynb # task5代码
│   │       
│   ├───resources/
│   │   │   stopword.txt # 停用词列表
│   │   │   user_dict.txt # 用户词典，用于分词
│   │   │   
│   │   └───cookie/ # 存放在爬取时需要的cookie
│   │           bilibili.txt 
│   │           weibo.txt
│   │           
│   └───task2/
│           bilibili_spider.py # B站爬虫
│           common.py # 微博爬虫所需函数库
│           weibo_spider.py # 微博爬虫
│           
└───result/
    ├───task2/ # 原始评论数据，CSV格式
    │   ├───bilibili/ 
    │   │       1040426196509130802_3.csv
    │   │       1040427588061757445_3.csv
    │   │       1040770506852139015_3.csv
    │   │       1041157251486711814_3.csv
    │   │       1041173142852075527_3.csv
    │   │       1041434659100033048_3.csv
    │   │       1041512513966964738_3.csv
    │   │       
    │   └───weibo/
    │           Ph0obiPYa_1.csv
    │           Ph0qBpntb_1.csv
    │           Ph98uucbM_1.csv
    │           PhiXC24Eo_1.csv
    │           PhjmChGI7_1.csv
    │           Phq0IBkx5_1.csv
    │           PhrZd1Qey_1.csv
    │           
    ├───task3/ # 数据汇总与可视化结果
    │       bilibili_total_comments.csv # B站所有评论汇总
    │       B站_bar_chart.png
    │       B站_daily_wordcloud.png
    │       B站_kde_plot.png
    │       B站_total_wordcloud.png
    │       weibo_total_comments.csv # 微博所有评论汇总
    │       微博_bar_chart.png
    │       微博_daily_wordcloud.png
    │       微博_kde_plot.png
    │       微博_total_wordcloud.png
    │       
    ├───task4/  # LDA主题建模可视化
    │       weibo_lda_visualization.html # 可交互的LDA模型可视化（HTML）
    │       weibo_lda_visualization.png # 上述可视化的静态截图
    │       
    └───task6/ # 情感分析结果
            wbemotion.csv # 微博前20条评论的情感分析结果（CSV格式）
```

## 致谢
本项目在数据采集部分借鉴并使用了以下开源项目的部分代码，特此致谢：
[WeiboSpider](https://github.com/nghuyong/WeiboSpider)：高性能的微博爬虫框架，支持全站内容抓取。
[Bilibili_crawler](https://github.com/linyuye/Bilibili_crawler)：B站弹幕与评论爬取工具，适用于舆情分析与内容挖掘。
感谢上述项目的作者为开源社区做出的贡献。
