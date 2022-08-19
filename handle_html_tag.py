# coding=UTF8
import base64
import re
from html import unescape as html_unescape

import bbcode
from pyquery import PyQuery as Pq

from ....config import config

from PIL import Image, ImageFont, ImageDraw
import time
import shutil

# 处理 bbcode
async def handle_bbcode(html: Pq) -> str:
    rss_str = html_unescape(str(html))

    # issue 36 处理 bbcode
    rss_str = re.sub(
        r"(\[url=[^]]+])?\[img[^]]*].+\[/img](\[/url])?", "", rss_str, flags=re.I
    )

    # 处理一些 bbcode 标签
    bbcode_tags = [
        "align",
        "b",
        "backcolor",
        "color",
        "font",
        "size",
        "table",
        "tbody",
        "td",
        "tr",
        "u",
        "url",
    ]

    for i in bbcode_tags:
        rss_str = re.sub(rf"\[{i}=[^]]+]", "", rss_str, flags=re.I)
        rss_str = re.sub(rf"\[/?{i}]", "", rss_str, flags=re.I)

    # 去掉结尾被截断的信息
    rss_str = re.sub(
        r"(\[[^]]+|\[img][^\[\]]+) \.\.\n?</p>", "</p>", rss_str, flags=re.I
    )

    # 检查正文是否为 bbcode ，没有成对的标签也当作不是，从而不进行处理
    bbcode_search = re.search(r"\[/(\w+)]", rss_str)
    if bbcode_search and re.search(rf"\[{bbcode_search.group(1)}", rss_str):
        parser = bbcode.Parser()
        parser.escape_html = False
        rss_str = parser.format(rss_str)

    return rss_str


# HTML标签等处理
async def handle_html_tag(html: Pq) -> str:
    rss_str = html_unescape(str(html))

    # 有序/无序列表 标签处理
    for ul in html("ul").items():
        for li in ul("li").items():
            li_str_search = re.search("<li>(.+)</li>", repr(str(li)))
            rss_str = rss_str.replace(
                str(li), f"\n- {li_str_search.group(1)}"  # type: ignore
            ).replace("\\n", "\n")
    for ol in html("ol").items():
        for index, li in enumerate(ol("li").items()):
            li_str_search = re.search("<li>(.+)</li>", repr(str(li)))
            rss_str = rss_str.replace(
                str(li), f"\n{index + 1}. {li_str_search.group(1)}"  # type: ignore
            ).replace("\\n", "\n")
    rss_str = re.sub("</(ul|ol)>", "\n", rss_str)
    # 处理没有被 ul / ol 标签包围的 li 标签
    rss_str = rss_str.replace("<li>", "- ").replace("</li>", "")

    # <a> 标签处理
    for a in html("a").items():
        a_str = re.search(
            r"<a [^>]+>.*?</a>", html_unescape(str(a)), flags=re.DOTALL
        ).group()  # type: ignore
        if a.text() and str(a.text()) != a.attr("href"):
            # 去除微博超话
            if re.search(
                r"https://m\.weibo\.cn/p/index\?extparam=\S+&containerid=\w+",
                a.attr("href"),
            ):
                rss_str = rss_str.replace(a_str, "")
            # 去除微博话题对应链接 及 微博用户主页链接，只保留文本
            elif ("weibo.cn" in a.attr("href") and a.children("span.surl-text")) or (
                "weibo.com" in a.attr("href") and a.text().startswith("@")
            ):
                rss_str = rss_str.replace(a_str, a.text())
            else:
                rss_str = rss_str.replace(a_str, f" {a.text()}: {a.attr('href')}\n")
        else:
            rss_str = rss_str.replace(a_str, f" {a.attr('href')}\n")

    # 处理一些 HTML 标签
    html_tags = [
        "b",
        "blockquote",
        "code",
        "dd",
        "del",
        "div",
        "dl",
        "dt",
        "em",
        "font",
        "i",
        "iframe",
        "ol",
        "p",
        "pre",
        "s",
        "small",
        "span",
        "strong",
        "sub",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "u",
        "ul",
        "html",
        "body",
    ]

    # <p> <pre> 标签后增加俩个换行
    for i in ["p", "pre"]:
        rss_str = re.sub(f"</{i}>", f"</{i}>\n\n", rss_str)

    # 直接去掉标签，留下内部文本信息
    for i in html_tags:
        rss_str = re.sub(f"<{i} [^>]+>", "", rss_str)
        rss_str = re.sub(f"</?{i}>", "", rss_str)

    rss_str = re.sub(r"<(br|hr)\s?/?>|<(br|hr) [^>]+>", "\n", rss_str)
    rss_str = re.sub(r"<h\d [^>]+>", "\n", rss_str)
    rss_str = re.sub(r"</?h\d>", "\n", rss_str)

    # 删除图片、视频标签
    rss_str = re.sub(
        r"<video[^>]*>(.*?</video>)?|<img[^>]+>", "", rss_str, flags=re.DOTALL
    )   

    # 去掉多余换行
    while "\n\n\n" in rss_str:
        rss_str = rss_str.replace("\n\n\n", "\n\n")
    rss_str = rss_str.strip()

    if 0 < config.max_length < len(rss_str):
        rss_str = rss_str[: config.max_length] + "..."


    # 文字转图片
    text = rss_str
    fontSize = 28
    lines = []
    line = u''
    fontPath = r"C:\Windows\Fonts\simhei.ttf"
    font = ImageFont.truetype(fontPath, fontSize)
    text = re.sub('\\n', '骉', text)
    for word in text:
        if word == '骉':
            lines.append(line)
            line = u''
            continue
        if font.getsize(line + word)[0] >= 480:
            lines.append(line)
            line = u''
            line += word
        else:
            line = line + word
    lines.append(line)
    line_height = (font.getsize(text)[1]) + 15
    img_height = line_height * (len(lines) + 1)
    im = Image.new("RGB", (540, line_height * (len(lines) + 1)), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    x, y = 30, 30
    for line in lines:
        dr.text((x, y), line, font=font, fill="#696969")
        y += line_height
    timeline = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    if time.strftime('%H%M',time.localtime(time.time())) == '0000':
        shutil.rmtree(filepath)
        os.mkdir(filepath)
        
    im.save(".\RSS\%s.JPEG" % timeline, 'JPEG', subsampling=0, quality=100)
    with open(".\RSS\%s.JPEG" % timeline,"rb") as f:
        img_data = f.read()
        base64_data = base64.b64encode(img_data)
        base64_str = str(base64_data, "utf-8")
        base_str = 'base64://' + base64_str
        cq_img ='[CQ:image,file=' + base_str + ',cache=1]'
    URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
    urls = re.findall(URL_REGEX,rss_str)
    input_info = cq_img
    for url in urls:
        input_info = input_info + '\n' + url
    return input_info

