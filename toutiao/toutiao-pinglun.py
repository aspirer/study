import re  

  
# 准备aaa.HTML文件的步骤：
# 1. 打开头条号评论管理页
# 2. 滚动到想要的位置
# 3. 另存为mhtml文件
# 4. 用Google Chrome打开mhtml文件
# 5. 找到msg-list-part read这个class
# 6. 右键，以html格式修改
# 7. 复制要修改的内容，保存到aaa.html文本文件中

with open('aaa.html', 'r') as f:  
    text = f.read()

matches = re.findall(r'<div class="msg-item-body">(.+?)</div>', text)
  
for match in matches:  
    match = re.sub(r'<i.*?</i>', '', match)
    print(match)  
