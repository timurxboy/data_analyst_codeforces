from selenium import webdriver

driver = webdriver.Chrome()  # or webdriver.Firefox()
driver.get("https://codeforces.com/problemset/status/4/problem/B/page/1")
response = driver.page_source
print(type(response))

driver.quit()
