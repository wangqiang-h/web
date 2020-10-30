import time
import re
import base64
import json
import sys
from selenium.webdriver import ActionChains
from get_code_position import get_position
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

BrowsermobPath = r'D:\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat'
Login12306Url = "https://kyfw.12306.cn/otn/resources/login.html"
UserName = '*****@qq.com'
PassWord = '*****'


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
        all_position_list = get_position(binary_raw_image)
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


if __name__ == '__main__':
    Login12306()
