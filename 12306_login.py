import time
from selenium.webdriver import ActionChains
from get_code_position import get_position
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
import re
import json
import sys
import random

server = Server(r'D:\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat')
server.start()
proxy = server.create_proxy(params={'trustAllServers': 'true'})
chrome_options = Options()
chrome_options.add_argument('--proxy-server={0}'.format(proxy.proxy))
# chrome_options.add_argument(
#     "user-agent=User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36")

browser = webdriver.Chrome(chrome_options=chrome_options)
proxy.new_har("new_har", options={'captureHeaders': True, 'captureContent': True})

url = "https://kyfw.12306.cn/otn/resources/login.html"
browser.get(url)
browser.implicitly_wait(1)  # 静默等待最大5秒，保证页面加载完毕
browser.maximize_window()  # 窗口最大化

browser.find_elements_by_link_text("账号登录")[0].click()

binary_raw_image = b''
time.sleep(1)

result = proxy.har
for entry in result['log']['entries']:
    url = entry['request']['url']
    content = entry['response']['content']
    if '/passport/captcha/captcha-image64' in url:
        print(url, content)
        if 'text' not in content:
            continue
        search_result = re.search(r'{.*}', content["text"])
        base64_raw_image = json.loads(search_result.group())["image"]
        binary_raw_image = base64.b64decode(base64_raw_image)
        break

if not binary_raw_image:
    print('not find binary_raw_image')
    sys.exit()

all_list = get_position(binary_raw_image)
print("get parse", all_list)
code_img_ele = browser.find_element_by_xpath('//*[@id="J-loginImg"]')

# 遍历位置列表,使用动作链对每一个列表元素对应的x，y指定的位置进行点击操作
for l in all_list:
    x = l[0]
    y = l[1]
    ActionChains(browser).move_to_element_with_offset(code_img_ele, x, y).click().perform()  # 动作链
    time.sleep(0.2)

# 输入用户名密码
browser.find_element_by_id('J-userName').send_keys('948829164@qq.com')
browser.find_element_by_id('J-password').send_keys('948829164wq')
browser.find_elements_by_link_text("立即登录")[0].click()

time.sleep(600)

# 加入动作链
div_tag = browser.find_element_by_xpath('//*[@id="nc_1_wrapper"]')

# 对div_tag进行滑动操作
action = ActionChains(browser)  # 实例化一个动作对象
action.click_and_hold(div_tag)  # 点击且长按不放

for _ in range(10):
    action.move_by_offset(34, 0)
    action.pause(0.05)

action.perform()

action.release()

time.sleep(600)

proxy.close()

browser.quit()
