import time
import re
import base64
import json
import sys
import requests
from selenium.webdriver import ActionChains
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

BrowsermobPath = r'D:\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat'
Login12306Url = "https://kyfw.12306.cn/otn/resources/login.html"
# 打码服务器的搭建 参照https://github.com/YinAoXiong/12306_code_server
CodeServer12306 = "http://192.168.32.3:8000/verify/base64/"
UserName = '***@qq.com'
PassWord = '***'


class Login12306:
    def __init__(self):
        self.server = Server(BrowsermobPath)
        self.server.start()
        self.proxy = self.server.create_proxy(params={'trustAllServers': 'true'})
        self.proxy.new_har("new_har", options={'captureHeaders': True, 'captureContent': True})

        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--proxy-server={0}'.format(self.proxy.proxy))
        options.add_experimental_option('excludeSwitches',
                                        ['enable-automation'])

        self.browser = webdriver.Chrome(chrome_options=options)
        self.browser_wait = WebDriverWait(self.browser, 10)

        try:
            self.startlogin()
            time.sleep(300)
        finally:
            self.close()

    def startlogin(self):
        self.browser.get(Login12306Url)
        # 参考https://blog.csdn.net/weixin_44685869/article/details/105602629 不加过不了阿里的验证
        script = 'Object.defineProperty(navigator,"webdriver",{get:() => false,});'
        self.browser.execute_script(script)
        self.browser.maximize_window()

        login_element = self.browser_wait.until(EC.presence_of_element_located((By.LINK_TEXT, "账号登录")))
        login_element.click()
        code_img_element = self.browser_wait.until(EC.presence_of_element_located((By.ID, "J-loginImg")))
        binary_raw_image = b''
        for _ in range(10):
            binary_raw_image = self.getCaptchaImage()
            if binary_raw_image:
                break
            time.sleep(0.1)
        if not binary_raw_image:
            print("can not capture data of captcha image")
            self.close()
            sys.exit(-1)
        self.ProcessCaptcha(binary_raw_image, code_img_element)
        self.ProcessSlideBlock()

    def getCaptchaImage(self):
        # 抓包的方法比截图的方法更简单
        binary_raw_image = b''
        result = self.proxy.har
        for entry in result['log']['entries']:
            url = entry['request']['url']
            content = entry['response']['content']
            if '/passport/captcha/captcha-image64' in url and 'text' in content:
                search_result = re.search(r'{.*}', content["text"])
                base64_raw_image = json.loads(search_result.group())["image"]
                binary_raw_image = base64.b64decode(base64_raw_image)
                break

        return binary_raw_image

    def ProcessCaptcha(self, binary_raw_image, code_img_element):
        all_position_list = self.get_position(binary_raw_image)
        print('get image postion %s ' % all_position_list)

        for x, y in all_position_list:
            ActionChains(self.browser).move_to_element_with_offset(code_img_element, x, y).click().perform()
            time.sleep(0.2)

        self.browser.find_element_by_id('J-userName').send_keys(UserName)
        self.browser.find_element_by_id('J-password').send_keys(PassWord)
        login_element = self.browser_wait.until(EC.presence_of_element_located((By.LINK_TEXT, "立即登录")))
        login_element.click()

    def ProcessSlideBlock(self):
        div_tag = self.browser_wait.until(EC.presence_of_element_located((By.ID, "nc_1_n1z")))
        action = ActionChains(self.browser)
        action.click_and_hold(div_tag)
        # for _ in range(10):
        #     action.move_by_offset(30, 0)
        #     action.pause(0.1)
        action.move_by_offset(300, 0)
        action.perform()
        action.release()

    def close(self):
        self.proxy.close()
        self.browser.quit()
        self.server.stop()

    def get_position(self, pic_raw_data):
        r = requests.post(url=CodeServer12306,
                          data={"imageFile": base64.b64encode(pic_raw_data)})
        result = r.json()
        select = result["data"]  # {'code': 0, 'data': ['6', '8'], 'massage': '识别成功'}

        post = []
        offsetsX = 0  # 选择的答案的left值,通过浏览器点击8个小图的中点得到的,这样基本没问题
        offsetsY = 0  # 选择的答案的top值
        for ofset in select:
            if ofset == '1':
                offsetsY = 77
                offsetsX = 40
            elif ofset == '2':
                offsetsY = 77
                offsetsX = 112
            elif ofset == '3':
                offsetsY = 77
                offsetsX = 184
            elif ofset == '4':
                offsetsY = 77
                offsetsX = 256
            elif ofset == '5':
                offsetsY = 149
                offsetsX = 40
            elif ofset == '6':
                offsetsY = 149
                offsetsX = 112
            elif ofset == '7':
                offsetsY = 149
                offsetsX = 184
            elif ofset == '8':
                offsetsY = 149
                offsetsX = 256
            else:
                pass
            post.append([offsetsX, offsetsY])
        return post


if __name__ == '__main__':
    Login12306()
