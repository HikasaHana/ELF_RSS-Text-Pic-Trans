# ELF_RSS-Text-Pic-Trans
基于@Quan666已有项目ELF_RSS的文字转图片改进，目的在于防止tx和谐。项目链接：https://github.com/Quan666/ELF_RSS

是随便在网上找相关代码copy出来的缝合怪，免去需要的人去缝合的时间。
使用方法：替换ELF_RSS-2.0\src\plugins\ELF_RSS2\RSS\routes\Parsing\handle_html_tag.py，根据注释作相应修改即可使用。转换后的图片保存在本地，做了发送前清理图片文件夹的功能，需要本地备份的自行删除。

实现功能：
  文字转图片输出；
  单独抓取url以文本发送；
  
注：此修改只对ELF_RSS的文字作处理，RSSHub附加的标题不做转换，要防止因为订阅用户名被风控请自行在RSSHub相应路由做修改。如果都作修改后依然触发风控，多半是发了涩图。
