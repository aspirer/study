
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# 职位关键词
JOB = "分布式块存储"

# 保存的文件名
file_name = "companys-%s.csv" % JOB
csv = open(file_name, 'w+')
csv.write('职位名称,公司名称,公司类型,融资情况,公司规模\n')  # 标题栏

# Create an instance of Chrome WebDriver
browser = webdriver.Chrome('./chromedriver')

'''  地区编码：
全国:410
上海:020
杭州:070020
苏州:060080
南京:060020
'''
CITYS = ["410", "020", "070020", "060080", "060020"]
PAGES = 10  # 最多抓取几页内容，貌似猎聘默认最多10页
WAIT_PAGE_SEC = 5  # 等待网页刷新完成时间，其实还有一个函数可以用来检查页面是否刷新完毕，懒得改了

for CITY in CITYS:
    URL = 'https://www.liepin.com/zhaopin/?city=%s&dq=%s&pubTime=&currentPage=0&pageSize=40&key=%s' % (CITY, CITY, JOB)
    browser.get(URL)

    count = 0
    while (count < PAGES):
        count += 1
        time.sleep(WAIT_PAGE_SEC)

        job_list = browser.find_element(By.CLASS_NAME, "job-list-box")
        job_titles = job_list.find_elements(By.CLASS_NAME, "job-title-box")  # 职位标题
        titles = [j.text.replace('\n', '') for j in job_titles]
        com_info_box = job_list.find_elements(By.CLASS_NAME, "job-company-info-box") # 公司信息列表
        i = 0
        for com in com_info_box:  # 遍历公司列表
            com_name = com.find_element(By.CLASS_NAME, "company-name").text  # 公司名称
            com_tags = com.find_elements(By.CLASS_NAME, "company-tags-box")  # 公司标签

            tags = com_tags[0].find_elements(By.TAG_NAME, 'span')
            com_tag = [tag.text for tag in tags]
            if len(com_tag) == 3:   # 有无融资情况标签
                line = ','.join(com_tag)
            else:
                line = ', ,'.join(com_tag)

            line = titles[i] + ',' + com_name + ',' + line + '\n'  # 一条完整的公司信息
            i += 1

            csv.write(line)  # 保存到文件

        button = browser.find_elements(By.CLASS_NAME, "ant-pagination-item-link")[-1]
        if button.is_enabled():  # 是否可以点下一页，也就是是否职位已经展示完了
            button.click()
        else:
            print("该区域所有职位已遍历完！\n")
            break

csv.close()
browser.quit()
print("正常结束！\n")