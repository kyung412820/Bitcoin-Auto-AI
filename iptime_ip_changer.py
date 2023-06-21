import time
from selenium import webdriver

class IptimeDriver:
	def __init__(self, _username = "admin", _password = "neolee3772", _temps_a_attendre = 8):
		# See https://chromedriver.chromium.org/downloads
		# self.driver = webdriver.Chrome('chromedriver')
		self.driver = webdriver.Chrome()
		self.temps_a_attendre = _temps_a_attendre

		self.driver.get("http://192.168.0.1")
		self.driver.find_element_by_name("username").send_keys(_username)
		self.driver.find_element_by_name("passwd").send_keys(_password)
		self.driver.implicitly_wait(10)
		self.driver.find_element_by_id("submit_bt").click()
		self.driver.get("http://192.168.0.1/sess-bin/timepro.cgi?tmenu=netconf&smenu=wansetup")
		self.driver.implicitly_wait(10)

	def ChangerPartiellement(self, _list_adresse):
		change = False
		for n in range(6):
			if _list_adresse[n] < 0:
				continue
			elem = self.driver.find_element_by_name("hw_dynamic" + str(n + 1))
			elem.click()
			h = int(elem.get_attribute("value"), 16)
			if _list_adresse[n] != h:
				change = True
				r = hex(_list_adresse[n])[2:].upper()
				if len(r) < 2:
					r = '0' + r
				elem.send_keys(r)
				self.driver.find_element_by_id("appbtn").click()
				self.driver.implicitly_wait(10)

		if change:
			time.sleep(self.temps_a_attendre)

	def __del__(self):
		self.driver.get("http://192.168.0.1/sess-bin/login_session.cgi?logout=1")
		self.driver.quit() 