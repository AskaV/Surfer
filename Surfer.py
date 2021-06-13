from logging import PercentStyle
from os import name
from time import sleep                                             
from typing import Sized
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote import webelement
from selenium.webdriver.common.by import By                        # page loading
from selenium.webdriver.support.wait import WebDriverWait          # page loading
from selenium.webdriver.support import expected_conditions as EC   # page loading
from selenium.webdriver import ActionChains                        # to send key combinations
from selenium.webdriver.common.keys import Keys                    # to send key combinations

import re # это регулярка
import codecs
import json #read\write json file
import os

class CWebSurfer:
    def __init__(self):
        self.url = ''
        self.login = ''
        self.pwd = ''
        self.category = dict()
        self.driver = webdriver.Chrome(r"chromedriver.exe")
        self.wait = WebDriverWait(self.driver, 10)
        self.black_list = []
        self.unknown_category = dict()
        self.log_path = ''
        self.category_filter = []
        self.category_link = dict()

    def setLogPath(self, path):
        self.log_path = path
        if os.path.exists(path):
            os.remove(path)

    def log(self, text):
        if self.log_path:
            with codecs.open(self.log_path, 'a', 'utf-8') as log_file:
                log_file.write(text + '\n')

    def readUserData(self, path, cat_filter_path):
        aLine = []
        with open(path, 'r') as file:
            aLine = file.readlines()

        self.url = aLine[0].rsplit()[0]
        self.login = aLine[1].rsplit()[0]
        self.pwd = aLine[2].rsplit()[0]

        aLine = []
        with codecs.open(cat_filter_path, 'r', 'utf-8') as cat_file:
            aLine = cat_file.readlines()

        for line in aLine:
            self.category_filter.append(line.rsplit()[0].lower())
            

    def readCategory(self, folder, link_path):
        for root, dirs, files in os.walk(folder):
            for name in files:
                j_file = os.path.join(root, name) # root = F:\Git\HSiteSurfer\HS_JSON_FILES; name = Компьютеры, Сети; root\name
                with codecs.open(j_file, 'r', 'utf-8') as json_file:
                    data = json.load(json_file)
                    new_dict = dict((k.lower(), v) for k, v in data.items())
                    self.log(name + ' loaded')
                    self.category[os.path.splitext(name)[0].lower()] = new_dict
        
        with codecs.open(link_path, 'r', 'utf-8') as json_file:
            self.category_link = json.load(json_file)
            self.log(link_path + ' loaded')

    def openUrl(self):
        self.driver.get(self.url) #get site URL from file
        self.driver.find_element_by_name("_username").send_keys(self.login) #get login from file
        self.driver.find_element_by_name("_password").send_keys(self.pwd) #get psw from file
        self.driver.find_element_by_name("_submit").click()        
        self.wait.until(EC.element_to_be_clickable((By.ID, 'approve-action')))

    def _getShopsList(self):
        aMap = dict()
        dropdown_menu = self.driver.find_element_by_xpath('//*[@id="page-content-wrapper"]/div/div/div/div[1]/div/div/div[1]/div/div/select')
        digit = re.compile(r'\(\d+\)')
        for option in dropdown_menu.find_elements_by_tag_name('option'):
            shop_name = re.sub(r'\s*\(\d+\)', '', option.text).lower() 
            if shop_name not in self.category_filter: #filter shops that are not on my list
                continue
            if shop_name in self.black_list:
                continue
            
            result = digit.search(option.text)
            if result:        
                count = int(result.group(0)[1:-1])
                aMap[shop_name] = count 

        return aMap

    def _chooseFastShop(self):
        aMap = self._getShopsList()
        min = 30000
        text = '' #make an empty text
        for key,value in aMap.items():
            if value < min:
                min = value
                text = key
        fast_shop = ''
        shop = self.driver.find_element_by_xpath('//*[@id="page-content-wrapper"]/div/div/div/div[1]/div/div/div[1]/div/div/select')
        for option in shop.find_elements_by_tag_name('option'):
            if text.lower() in option.text.lower():
                fast_shop = text.lower()
                option.click() # select() in earlier versions of webdriver
                break
        
        sleep(5) #todo: check KNOPKA ZAGRYZKA
        return fast_shop

    def _apply(self):
        self.driver.find_element_by_xpath('//*[@id="approve-action"]').click()

    def _addProposition(self, file, category, name):
        #todo: check exists of category in self.unknown_category and add name if category exists
        cat = dict()
        cat[category] = name
        self.unknown_category[file] = cat


        #adding a proposal
    def _appendProposition(self, file, category, name):  
        cat = dict()
        cat[category] = name
        self.unknown_category[file][category] = name

    def appendCatinList(self, categoryName,  hotL_cat, shop_description):
        if categoryName in self.unknown_category:
            print('category found in falo on addeded prop: \'' + categoryName + '\'')
            #os.system("pause")
            self._appendProposition(categoryName, hotL_cat, shop_description)
            return True
        elif hotL_cat in self.unknown_category:
            print('category found in falo on addeded prop: \'' + hotL_cat + '\'')
            #os.system("pause")
            self._appendProposition(hotL_cat, hotL_cat, shop_description)
            return True
        return False
    
    def markCorrectRows(self):
        shop = self._chooseFastShop()
        self.log('Choosen shop: ' + shop)
        # Find our table
        table_id = self.driver.find_element_by_xpath('//*[@id="jqGrid"]') 
        #1) find row Count
        aRows = table_id.find_elements_by_xpath('//*[@id="jqGrid"]/tbody/tr') # empty row
        categoryName = ''   #Categories of gray row
        marked_row_count = 0
        for tableCoutn in range(2, len(aRows) + 1):   # 0-headers, 1-empty, 2-gray, 3-white
            #check row for color(grey or white)
            tableRow = table_id.find_elements_by_xpath('//*[@id="jqGrid"]/tbody/tr[' + str(tableCoutn) + ']') #find 2-nd gray row
            tableColum = tableRow[0].find_elements_by_tag_name('td')
            if len(tableColum) == 1:
                #3) exclude grey rows (and save category name)
                categoryName = tableColum[0].text.split(' »')[0].lower()
                if '→' in categoryName:
                    categoryName = categoryName.split(' →')[0].lower()
                bFound = False
                for key, value in self.category_link.items():
                    if bFound:
                        break
                    for v in value:
                        if categoryName in v.lower():
                            categoryName = key.lower()
                            bFound = True
                            break
                continue
            else:
                columsInRow = tableRow[0].find_elements_by_tag_name('td')
                shop_cat = columsInRow[2].text.lower()
                hotL_cat = columsInRow[3].text.lower()
                shop_description = columsInRow[4].text.lower()
                if categoryName not in self.category:
                    if self.appendCatinList(categoryName,  hotL_cat, shop_description):
                        continue

                    print('category not found: \'' + categoryName + ' in shop :' + shop + '\'') 
                    self._addProposition(categoryName, hotL_cat, shop_description)
                    continue

                if hotL_cat not in self.category[categoryName]:
                    if self.appendCatinList(categoryName,  hotL_cat, shop_description):
                        continue
                    
                    print('sub-category not found: \'' + hotL_cat + + ' in shop :' + shop + '\'')  
                    self._addProposition(categoryName, hotL_cat, shop_description)
                    continue


                list_available_sinonims = self.category[categoryName][hotL_cat]
                bFound = False
                for sin in list_available_sinonims: # itearate all available sinonims
                    if sin.lower() in shop_description: 
                        marked_row_count += 1
                        bFound = True
                        self.log('SELECTING cat:' + categoryName + ', hotline cat:' + hotL_cat + ', description:' + shop_description)
                        ActionChains(self.driver).key_down(Keys.CONTROL).click(columsInRow[0]).key_up(Keys.CONTROL).perform()
                        break
                if not bFound:
                    self._addProposition(categoryName, hotL_cat, shop_description)
        if marked_row_count: #marked_row_count != 0
            self.log(shop + ' done')
            print('Click aplly?(y/n)')
            input_data = input()
            if input_data.lower() == 'y':
                self._apply() #click apply
                self.log('applyed!!!')
            else:
                self.log('go next shop')
                sleep(5)
        else:
            self.black_list.append(shop)

    def writeNewCat(self, path):
        with open(path, "w", encoding='utf8') as write_file:
            json.dump(self.unknown_category, write_file, ensure_ascii=False, indent=4)

