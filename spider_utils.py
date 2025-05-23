from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import time
import re
from zhipuai import ZhipuAI
import psutil
import os
from itertools import zip_longest
import random
def kill_old_driver(pid_path="driver.pid"):
    if not os.path.exists(pid_path):
        return
    try:
        with open(pid_path, "r") as f:
            pid = int(f.read())
        if psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            proc.kill()
            print(f"[INFO] Killed old driver PID: {pid}")
        os.remove(pid_path)
    except Exception as e:
        print(f"[ERROR] Failed to kill old driver: {e}")
def smiliray(text,scenic_name):
    

    client = ZhipuAI(api_key="684ccab31547156de2c15bfc62640e68.48YE6a8vTjp9gBbB") 
    response = client.chat.completions.create(
    model="glm-4-flash",  # 填写需要调用的模型编码
    messages=[
        {"role": "system", "content": "你是一个景区相似度匹配专家，接受用户输入的景区名称和查找到的景区名称，输出一个得分（0-1），得分越高越相似，直接输出0.0-1.0之间的数字，不能有其他任何文字。"},
        {"role": "user", "content":f"计算{text}和{scenic_name}的相似度，输出一个得分，得分越高越相似，直接输出0.0-1.0之间的数字，不能有其他任何文字。"}
    ],
    )
    return float(response.choices[0].message.content.strip())
# def fetch_province_html(province, headless=True, wait_time=10):
    kill_old_driver()
    options = Options()
    if headless:
        options.add_argument("--headless")  # 不显示浏览器窗口
        options.add_argument("--disable-gpu")
     # 关键 Headers 模拟
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/123.0.0.0 Safari/537.36')

    # 反检测常用选项
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    
    pid = driver.service.process.pid
    with open('./driver.pid', "w") as f:
        f.write(str(pid))
    print(f"[INFO] Created driver with PID: {pid}")
    wait = WebDriverWait(driver, wait_time)

    try:
        # Step 1: 打开首页
        driver.get("https://travel.qunar.com/?from=header")

        # Step 2: 找到 div.bg
        bg_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bg")))

        # Step 3: 获取 div 内的 input 和 a
        input_box = bg_div.find_element(By.TAG_NAME, "input")
        search_btn = bg_div.find_element(By.TAG_NAME, "a")

        # Step 4: 设置输入值并点击
        input_box.clear()
        input_box.send_keys(province)
        search_btn.click()

        # Step 5: 等待页面加载完成（以 li 元素为标志）
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.list_item.clrfix')))

        # Step 6: 返回跳转后的 HTML
        return driver.page_source,driver
    except Exception as e:
        print(e)
def fetch_province_html(province, headless=True, wait_time=10, max_retry=3):
    kill_old_driver()

    for attempt in range(max_retry):
        try:
            options = Options()
            if headless:
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")

            # 伪装成浏览器
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/123.0.0.0 Safari/537.36')

            # 反自动化检测
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(options=options)

            # 去掉 navigator.webdriver 特征
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            })

            pid = driver.service.process.pid
            with open('./driver.pid', "w") as f:
                f.write(str(pid))
            print(f"[INFO] Created driver with PID: {pid}")

            wait = WebDriverWait(driver, wait_time)

            # Step 1: 打开首页
            driver.get("https://travel.qunar.com/?from=header")
            time.sleep(random.uniform(2, 4))  # 模拟人类行为

            # Step 2: 找到 div.bg
            bg_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bg")))

            # Step 3: 获取 div 内的 input 和 a
            input_box = bg_div.find_element(By.TAG_NAME, "input")
            search_btn = bg_div.find_element(By.TAG_NAME, "a")

            # Step 4: 设置输入值并点击
            input_box.clear()
            input_box.send_keys(province)
            time.sleep(random.uniform(0.5, 1.5))
            search_btn.click()

            # Step 5: 等待结果页 li 元素加载
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.list_item.clrfix')))

            # Step 6: 返回 HTML 和 driver
            return driver.page_source, driver

        except Exception as e:
            print(f"[WARN] Attempt {attempt + 1} failed: {e}")
            if attempt == max_retry - 1:
                print("[ERROR] Max retries reached. Giving up.")
                return None, None
            time.sleep(random.uniform(3, 6))  # 重试等待
        # finally:
        #     # 如果页面失败，中间的 driver 需要关闭
        #     try:
        #         driver.quit()
        #     except:
        #         pass
def extract_place_more_link(html):
    soup = BeautifulSoup(html, 'html.parser')
    morebox = soup.find('div', class_='b_morebox')
    if morebox:
        link = morebox.find('a', {'data-beancon': 'placeResult_more'})
        if link and link.has_attr('href'):
            return link['href']
    return None

def find_scenic_href_from_paginated_list(driver, scenic_name, wait_time=10):
    wait = WebDriverWait(driver, wait_time)
    
    while True:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.list_item.clrfix')))
        li_items = driver.find_elements(By.CSS_SELECTOR, 'li.list_item.clrfix')

        for li in li_items:
            try:
                a_tag = li.find_element(By.CSS_SELECTOR, 'a.tit')
                # a_tag.text 会自动忽略 span.icon 的文本，返回纯文本"西岛"
                text = a_tag.text.strip()
                simliary = (smiliray(text,scenic_name))
                print(text,scenic_name,simliary)
                # print(simliary)
                if simliary>0.9 :
                    return a_tag.get_attribute('href'),driver
            except Exception as e:
                print(e)

        # 找下一页
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'a.next')
            print("找到下一页按钮")
            href = next_button.get_attribute('href')
            if href:
                driver.get(href)
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.list_item.clrfix')))
                with open("test.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                
            else:
                return None
        except:
            return None

def open_scenic_and_expand_ticket_options(driver, scenic_href, wait_time=15):
    wait = WebDriverWait(driver, wait_time)
    driver.get(scenic_href)

    # 保存初始页面方便调试
    # with open("detail_page_initial.html", "w", encoding="utf-8") as f:
    #     f.write(driver.page_source)

    try:
        # 找到"更多票种"按钮
        more_ticket_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//a[@class="txt" and contains(text(),"更多票种")]')
            )
        )

        # 点击按钮（用JS点击更稳定）
        driver.execute_script("arguments[0].click();", more_ticket_btn)

        # 等待"收起报价"按钮出现，代表票种展开成功
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//a[contains(@class,"txt") and contains(@class,"expand") and contains(text(),"收起报价")]')
            )
        )

        # 保存展开后的页面
        html_after_click = driver.page_source
       
        # print("成功展开票种内容")
        return html_after_click

    except Exception as e:
        print("❌ 在详情页点击更多票种失败:", e)
        print("当前URL:", driver.current_url)
        driver.save_screenshot("detail_page_error.png")
        with open("detail_page_error.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        return None
    
# 抽取小贴士
def extract_tips_text(driver):
    try:
        tips_div = driver.find_element(By.ID, "ts")
        # 找到 tips_div 里 class 包含 e_db_content_box 的 div
        content_div = tips_div.find_element(By.CSS_SELECTOR, "div.e_db_content_box")
        # 找到所有 p 标签，拼接它们的文本
        p_elements = content_div.find_elements(By.TAG_NAME, "p")
        texts = [p.text.strip() for p in p_elements if p.text.strip()]
        # 合并为一个字符串，换行分隔，或者根据需求返回列表
        tips_text = "\n".join(texts)
        return tips_text
    except Exception as e:
        print("提取小贴士失败:", e)
        return None
# def extract_tips_text(driver):
#     try:
#         tips_div = driver.find_element(By.ID, "ts")
#         # 取里面 class="e_db_content_box e_db_content_dont_indent" 的 <p> 标签文本
#         tips_text = tips_div.find_element(By.CSS_SELECTOR, "div.e_db_content_box > p").text.strip()
#         return tips_text
#     except Exception as e:
#         print("提取小贴士失败:", e)
#         return None
# 抽取票价信息
def extract_all_ticket_info(driver):
    tickets = []
    try:
        # 定位祖先div
        container = driver.find_element(By.CLASS_NAME, "e_ticket_info_box")
        # 找所有dl标签（无视class和style）
        dl_elements = container.find_elements(By.TAG_NAME, "dl")

        for dl in dl_elements:
            try:
                ticket_name = dl.find_element(By.TAG_NAME, 'dt').text.strip()
                old_price = dl.find_element(By.CSS_SELECTOR, 'dd.e_old_price del').text.strip()
                now_price = dl.find_element(By.CSS_SELECTOR, 'dd.e_now_price span.e_price_txt').text.strip()
                view_price_link = dl.find_element(By.CSS_SELECTOR, 'dd.e_view_price_box a.e_view_price').get_attribute('href')

                tickets.append({
                    'ticket_name': ticket_name,
                    'old_price': old_price,
                    'now_price': now_price,
                    'view_price_link': view_price_link
                })
            except Exception as e:
                print(f"解析单个票种失败: {e}")
                continue
    except Exception as e:
        print(f"找不到票价容器或解析失败: {e}")

    return tickets
# 抽取概要
def extract_texts_and_images(driver, container_id=None):
    """
    从页面中提取指定容器内 class="e_db_content_box" 下的所有<p>文本和<img>图片链接
    :param driver: selenium webdriver 对象
    :param container_id: 指定父容器id（如"gs"），若为None则取第一个e_db_content_box
    :return: (texts: list[str], images: list[str])
    """
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    if container_id:
        parent = soup.find(id=container_id)
        if not parent:
            return [], []
        container = parent.find('div', class_='e_db_content_box')
    else:
        container = soup.find('div', class_='e_db_content_box')

    if not container:
        return [], []

    texts = []
    images = []

    for p in container.find_all('p'):
        # 你可以选择只用纯文本，也可以保留部分标签，示例如下：
        # 纯文本：
        text = p.get_text(separator=' ', strip=True)
        if text:
            texts.append(text)

        # 保留内嵌HTML（示例，非必须）
        # html_str = str(p)
        # texts.append(html_str)

        # 提取图片
        for img in p.find_all('img'):
            src = img.get('src')
            if src:
                images.append(src)

    return texts, images
# def extract_texts_and_images(driver):
#     """
#     从driver当前页面中，提取class="e_db_content_box"里的所有<p>文本和<img>图片链接，
#     返回两个列表（文本列表，图片链接列表）

#     :param driver: selenium webdriver对象
#     :return: (texts: list[str], images: list[str])
#     """
#     html = driver.page_source
#     soup = BeautifulSoup(html, 'html.parser')
#     container = soup.find('div', class_='e_db_content_box')
#     if not container:
#         return [], []

#     texts = []
#     images = []

#     for elem in container.children:
#         if elem.name == 'p':
#             text = elem.get_text(strip=True)
#             if text:
#                 texts.append(text)
#             imgs = elem.find_all('img')
#             for img in imgs:
#                 src = img.get('src')
#                 if src:
#                     images.append(src)

#     return texts, images
# 抽取旅游时节
def extract_travel_season_text(driver):
    
    """
    提取id='lysj' 区块内的旅游时节文本内容

    :param driver: selenium webdriver对象
    :return: 旅游时节文本字符串，如果没找到返回空字符串
    """
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    section = soup.find('div', id='lysj')
    if not section:
        return ""

    content_box = section.find('div', class_='e_db_content_box')
    if not content_box:
        return ""

    return content_box.get_text(strip=True)
# 抽取交通指南01
def extract_traffic_guide_dict(driver):
    from bs4 import BeautifulSoup

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    section = soup.find('div', id='jtzn')
    if not section:
        return {}

    content_box = section.find('div', class_='e_db_content_box e_db_content_dont_indent')
    if not content_box:
        return {}

    result = {}
    current_key = None
    current_value_lines = []

    for p in content_box.find_all('p'):
        strong = p.find('strong')

        if strong and strong.get_text(strip=True):
            # 遇到新的标题，先保存上一条
            if current_key and current_value_lines:
                result[current_key] = '\n'.join(current_value_lines).strip()
                current_value_lines = []

            current_key = strong.get_text(strip=True)

            # 当前段落除strong标签外的文本（你这个HTML里是空的，暂不处理）
            strong.extract()
            remaining = p.get_text(strip=True)
            if remaining:
                current_value_lines.append(remaining)

        else:
            # 没有strong，当前内容段落，追加到当前key下
            text = p.get_text(strip=True)
            if text and current_key:
                current_value_lines.append(text)

    # 最后一组也保存
    if current_key and current_value_lines:
        result[current_key] = '\n'.join(current_value_lines).strip()

    return result

# def extract_traffic_guide_dict(driver):
    from bs4 import BeautifulSoup

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    section = soup.find('div', id='jtzn')
    if not section:
        return {}

    content_box = section.find('div', class_='e_db_content_box e_db_content_dont_indent')
    if not content_box:
        return {}

    result = {}
    current_key = None
    current_value_lines = []

    for p in content_box.find_all('p'):
        strong = p.find('strong')

        if strong and strong.get_text(strip=True):
            # 保存上一节内容
            if current_key and current_value_lines:
                result[current_key] = '\n'.join(current_value_lines).strip()
                current_value_lines = []

            current_key = strong.get_text(strip=True)

            # 抽取 strong 后同段落中的内容
            strong.extract()
            remaining = p.get_text(strip=True)
            if remaining:
                current_value_lines.append(remaining)

        elif current_key:
            text = p.get_text(strip=True)
            if text:
                current_value_lines.append(text)

    # 保存最后一节
    if current_key and current_value_lines:
        result[current_key] = '\n'.join(current_value_lines).strip()

    return result


    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    section = soup.find('div', id='jtzn')
    if not section:
        return {}

    content_box = section.select_one('div.e_db_content_box')
    if not content_box:
        return {}

    result = {}
    current_key = None
    current_value_lines = []

    for p in content_box.find_all('p'):
        strong = p.find('strong')
        text = p.get_text(strip=True)

        if strong and strong.get_text(strip=True):
            # 新 key 出现前保存前一个 key 的值
            if current_key and current_value_lines:
                result[current_key] = '\n'.join(current_value_lines).strip()
                current_value_lines = []

            current_key = strong.get_text(strip=True)
            # 如果 strong 后还有文字，也作为第一段加入（适配某些 <p><strong>公交</strong>内容</p> 情况）
            strong.extract()
            remaining_text = p.get_text(strip=True)
            if remaining_text:
                current_value_lines.append(remaining_text)
        else:
            # 内容部分
            if current_key and text:
                current_value_lines.append(text)

    # 收尾
    if current_key and current_value_lines:
        result[current_key] = '\n'.join(current_value_lines).strip()

    return result
# 抽取指南
# def extract_traffic_guide_dict(driver):
    from bs4 import BeautifulSoup

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    with open('test.html', 'w', encoding='utf-8') as f:
        f.write(html)
    traffic_section = soup.find('div', id='jtzn')
    if not traffic_section:
        return {}

    # 精确匹配 class 同时包含多个名称
    content_box = traffic_section.find('div', class_='e_db_content_box e_db_content_dont_indent')
    if not content_box:
        return {}

    result = {}
    current_key = None
    current_value_lines = []

    for p in content_box.find_all('p'):
        strong = p.find('strong')
        if strong:
            # 遇到新的 key，先存前面的值
            if current_key and current_value_lines:
                result[current_key] = '\n'.join(current_value_lines).strip()
                current_value_lines = []

            current_key = strong.get_text(strip=True)
        else:
            if current_key:
                text = p.get_text(strip=True)
                if text:
                    current_value_lines.append(text)

    # 最后一项也要保存
    if current_key and current_value_lines:
        result[current_key] = '\n'.join(current_value_lines).strip()

    return result
from bs4 import BeautifulSoup
# 抽取交通指南文本02
def extract_traffic_guide_text(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    section = soup.find('div', id='jtzn')
    if not section:
        return ""

    content_box = section.find('div', class_='e_db_content_box e_db_content_dont_indent')
    if not content_box:
        return ""

    # 用 .stripped_strings 抽取所有非空文本（会自动忽略多余空白）
    texts = list(content_box.stripped_strings)

    # 因为 <br> 是换行，但 .stripped_strings 会把它当分割，所以直接用空格拼接会丢失换行
    # 这里可以用content_box的直接内容，按 <br> 分割，保留换行
    parts = []
    for elem in content_box.children:
        if elem.name == 'br':
            parts.append('\n')  # 换行
        else:
            # elem可能是Tag或者NavigableString
            text = ''
            if hasattr(elem, 'get_text'):
                text = elem.get_text(strip=True)
            else:
                text = str(elem).strip()
            if text:
                parts.append(text)

    # 合并成字符串，连续多个换行合并成一个
    import re
    full_text = ''.join(parts)
    full_text = re.sub(r'\n+', '\n', full_text).strip()

    return full_text


# 假设html是你抓取的页面内容，调用方式：
# guide_text = extract_traffic_guide_text(html)
# print(guide_text)

# def extract_traffic_guide_dict(driver):
#     html = driver.page_source
#     soup = BeautifulSoup(html, 'html.parser')

#     section = soup.find('div', id='jtzn')
#     if not section:
#         return {}

#     content_box = section.select_one('div.e_db_content_box')
#     if not content_box:
#         return {}

#     result = {}
#     current_key = None
#     current_value_lines = []

#     for p in content_box.find_all('p'):
#         strong = p.find('strong')
#         if strong:
#             # 保存上一段内容
#             if current_key and current_value_lines:
#                 result[current_key] = '\n'.join(current_value_lines).strip()
#                 current_value_lines = []

#             current_key = strong.get_text(strip=True)
#         else:
#             text = p.get_text(strip=True)
#             if text and current_key:
#                 current_value_lines.append(text)

#     # 保存最后一段内容
#     if current_key and current_value_lines:
#         result[current_key] = '\n'.join(current_value_lines).strip()

#     return result

# def extract_traffic_guide_dict(driver):
#     html = driver.page_source
#     soup = BeautifulSoup(html, 'html.parser')

#     section = soup.find('div', id='jtzn')
#     if not section:
#         return {}

#     # 用select_one保证找到包含多个class的div
#     content_box = section.select_one('div.e_db_content_box')
#     if not content_box:
#         return {}

#     result = {}
#     current_key = None
#     current_value_lines = []

#     for p in content_box.find_all('p'):
#         strong = p.find('strong')
#         if strong and strong.get_text(strip=True):
#             # 存储上一组内容
#             if current_key:
#                 result[current_key] = '\n'.join(current_value_lines).strip()

#             current_key = strong.get_text(strip=True)
#             current_value_lines = []

#             # 移除strong标签后获取剩余文本
#             strong.extract()
#             remaining_text = p.get_text(strip=True)
#             if remaining_text:
#                 current_value_lines.append(remaining_text)
#         else:
#             text = p.get_text(strip=True)
#             if text:
#                 current_value_lines.append(text)

#     # 保存最后一个key的内容
#     if current_key:
#         result[current_key] = '\n'.join(current_value_lines).strip()

#     return result

# 抽取评论
import re
import requests
from bs4 import BeautifulSoup

def extract_comments(driver, page_size, page):
    url = driver.current_url
    poi_id = re.findall(r'\d+', url)[0]
    base_url = "https://travel.qunar.com/place/api/html/comments/poi/"
    api_url = f"{base_url}{poi_id}?poiList=true&sortField=1&rank=0&pageSize={page_size}&page={page}"

    try:
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()
        data_json = resp.json()

        if data_json.get('errcode') != 0:
            print(f"接口返回错误: {data_json.get('errmsg')}")
            return []

        html_content = data_json.get('data', '')
        if not html_content:
            print("没有评论内容，返回空列表")
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        comments_list = []

        comment_items = soup.find_all('li', class_='e_comment_item')
        for item in comment_items:
            user_tag = item.find('div', class_='e_comment_usr_name')
            user = user_tag.get_text(strip=True) if user_tag else ''

            # ✅ 提取完整评论内容
            content_div = item.find('div', class_='e_comment_content')
            if content_div:
                first_paragraph = content_div.find('p', class_='first')
                content = first_paragraph.get_text(strip=True) if first_paragraph else ''
            else:
                content = ''

            date_tag = item.find('div', class_='e_comment_add_info')
            date = ''
            if date_tag:
                date_li = date_tag.find('li')
                if date_li:
                    date = date_li.get_text(strip=True)

            imgs = []
            imgs_box = item.find('div', class_='e_comment_imgs_box')
            if imgs_box:
                img_tags = imgs_box.find_all('img', class_='cmt_img')
                imgs = [img['src'] for img in img_tags if img.has_attr('src')]

            # 解析评分
            star_box = item.find('div', class_='e_comment_star_box')
            rating = None
            if star_box:
                star_span = star_box.find('span', class_='cur_star')
                if star_span and star_span.has_attr('class'):
                    classes = star_span['class']
                    for cls in classes:
                        if cls.startswith('star_'):
                            try:
                                rating = int(cls.split('_')[1])
                            except:
                                rating = None

            comment_dict = {
                'user': user,
                'content': content,
                'date': date,
                'images': imgs,
                'rating': rating,
            }
            comments_list.append(comment_dict)

        return comments_list

    except requests.RequestException as e:
        print(f"请求异常: {e}")
        return []
    except ValueError as e:
        print(f"JSON解析失败: {e}")
        return []
def extrac_messages(province, scenic):
    html,driver = fetch_province_html(province)
    print("获取省份html")
    url = extract_place_more_link(html)
    driver.get(url)
    print("获取景点html")
    # with open('test.html', 'w', encoding='utf-8') as f:
    #     f.write(driver.page_source)
    scenic_href,driver = find_scenic_href_from_paginated_list(driver,scenic)
    html = open_scenic_and_expand_ticket_options(driver, scenic_href)

    # 抽取旅游攻略
    texts, images = extract_texts_and_images(driver)
    
    tickets_dict = extract_all_ticket_info(driver)
    season_text = extract_travel_season_text(driver)
    traffic_guide_dict = extract_traffic_guide_dict(driver)
    tips_text = extract_tips_text(driver)
    if len(traffic_guide_dict.keys()) == 0:
        text = extract_traffic_guide_text(driver)
        traffic_guide_dict = {"交通方式":text}
    text_image_pairs = list(zip_longest(texts, images))
    print(traffic_guide_dict)
    messages={
        "text_image_pairs": text_image_pairs,
        "tickets": tickets_dict,
        "season": season_text,
        "traffic_guide": traffic_guide_dict,
        "tips": tips_text,
    }
    
    
    return messages, driver  # 返回driver对象