from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def set_chrome_options() -> Options:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return chrome_options

if __name__ == "__main__":
    driver = webdriver.Chrome(options=set_chrome_options())
    # Do stuff with your driver
    driver.get("http://admin:soc-e@192.168.4.64/advanced.html?cfg=nvlan&attr=adv_conf")
    #WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Add VLAN']"))).click()
    #driver.find_element_by_xpath("//button[text()='Add VLAN']").click()
    #last = driver.find_element(By.XPATH, '//button[text()="Add VLAN"]').click()
    #last = driver.find_element(By.PARTIAL_LINK_TEXT, "Add VLAN").click()
    #last = driver.find_element(By.LINK_TEXT, "Add VLAN").click()
    print (driver.title)
    print (driver.current_url)
    driver.implicitly_wait(0.5)
    addVlan = driver.find_element(by=By.XPATH, value='/html/body/div/div[1]/section[2]/div[2]/div/section[1]/div[2]/div[3]/span[1]/button').click()
    driver.implicitly_wait(0.5)
    vlanId = driver.find_element(by=By.ID, value = 'vlan_id_nvlan_config_add_nvlan_config')
    vlanId.send_keys('2')
    vlanName = driver.find_element(by=By.ID, value='vlan_name_nvlan_config_add_nvlan_config')
    vlanName.send_keys('vlan python')
    selectAll = driver.find_element(by=By.ID, value= 'select_all_SWITCH_egressPorts').click()
    Add = driver.find_element(by=By.ID, value = 'btn-up-vlan').click()
    #last = driver.find_element(by=By.ID, value="trash_r_SWITCH_nvlan_0")
    #wait = WebDriverWait(driver, 10)
    #wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Add VLAN']"))).click()

    #inputElement = driver.find_element_by_id("vlan_id_nvlan_config_add_nvlan_config")
    #inputElement.send_keys('2') 
    #inputCheckbox = driver.find_element_by_id("select_all_SWITCH_egressPorts")
    #inputCheckbox.click()
    #WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Add']"))).click()
    driver.close()
