import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotVisibleException


class USDAscrape(object):

    def __init__(self, category, start_date, end_date, query=None):
        self.url = 'https://www.marketnews.usda.gov/mnp/ls-report-config'
        self.driver = webdriver.Chrome()
        self.category = category
        self.start_date = start_date
        self.end_date = end_date
        self.query = query


    def selenium_session(self):
        '''
        Opens a Chrome driver at the destination URL and proceeds to run the query
        and then scrape the tables on subsequent pages.
        '''
        self.driver.get(self.url)

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//select[@name='category']/option[text()='{}']".format(self.category)))).click()

        self.select_fields()

        self.driver.find_element_by_name('run').click()

        WebDriverWait(self.driver, 10)

        page_html = BeautifulSoup(self.driver.page_source, 'html.parser')
        tables = page_html.find_all('table',attrs={'class':'reportTable'})

        data = []
        data, columns = self.table_scrape(data,tables)

        #loops through all pages of data by checking for the 'Next' button and clicking if available
        while True:
                try:
                    next_elem = self.driver.find_element_by_xpath("//font[text()='Next']")
                    next_elem.find_element_by_xpath("..").click()

                    page_html = BeautifulSoup(self.driver.page_source, 'html.parser')
                    tables = page_html.find_all('table',attrs={'class':'reportTable'})
                    data, columns = self.table_scrape(data,tables)

                except:
                    break

        ## Quit the selenium sesssion
        self.driver.quit()

        # Writes result to CSV file
        filename = '{}_{}_{}.csv'.format(self.category,self.start_date.replace('/',''),self.end_date.replace('/',''))
        return self.generate_df(data,columns).to_csv(filename,index=False)


    def select_fields(self):
        '''
        Selects all possible menu values once the main query has been set
        '''
        self.set_category()

        ##Select all uses
        try:
            use_select = Select(self.driver.find_element_by_id('use'))

            for i in range(len(use_select.options)):
                use_select.select_by_index(i)
        except:
            pass

        ##Select all frame sizes
        try:
            fsize_select = Select(self.driver.find_element_by_id('fsize'))

            for i in range(len(fsize_select.options)):
                fsize_select.select_by_index(i)
        except:
            pass

        ##Select all muscle scores
        try:
            mscore_select = Select(self.driver.find_element_by_id('mscore'))

            for i in range(len(mscore_select.options)):
                mscore_select.select_by_index(i)
        except:
            pass

        ##Select all grades
        try:
            grade_select = Select(self.driver.find_element_by_id('grade'))

            for i in range(len(grade_select.options)):
                grade_select.select_by_index(i)
        except:
            pass

        ##Select all weight ranges - for categories with weight ranges
        try:
            wrange_select = Select(self.driver.find_element_by_id('wrange'))

            for i in range(len(wrange_select.options)):
                wrange_select.select_by_index(i)
        except:
            pass

        ##Set dates logic (depends on query supporting daily versus weekly)
        if self.category == 'Grain':
            if self.query['organic']=='Yes' and self.query['commodity'] != 'Hay':
                elem = self.driver.find_element_by_id('repDateWeeklyGrain')
                elem.click()
                elem.send_keys(self.start_date)

                elem2 = self.driver.find_element_by_id('endDateWeeklyGrain')
                elem2.click()
                elem2.send_keys(self.end_date)

            else:
                elem = self.driver.find_element_by_id('repDateGrain')
                elem.click()
                elem.send_keys(self.start_date)

                elem2 = self.driver.find_element_by_id('endDateGrain')
                elem2.click()
                elem2.send_keys(self.end_date)

        else:
            try:
                elem = self.driver.find_element_by_id('repDate')
                elem.click()
                elem.send_keys(self.start_date)

                elem2 = self.driver.find_element_by_id('endDate')
                elem2.click()
                elem2.send_keys(self.end_date)

            except ElementNotVisibleException:
                elem = self.driver.find_element_by_id('repDateWeekly')
                elem.click()
                elem.send_keys(self.start_date)

                elem2 = self.driver.find_element_by_id('endDateWeekly')
                elem2.click()
                elem2.send_keys(self.end_date)


    def table_scrape(self, data, tables):
        '''
        Scrapes each page in query result
        '''
        for table in tables:
            columns = []
            for row in table.find_all('tr',attrs={'class':'ReportsTableCell2'}):
                inner_list = [td.get_text().encode('utf-8') for td in row]

                if self.category == 'Beans, Peas, and Lentils':
                    table_header = table.find('tr', attrs={'class':'ReportsSubheader'}).get_text().encode('utf-8')
                    inner_list.extend([table_header])
                    data.append(inner_list)

                    columns = ['Week Ending Date','Location','Class','Variety','Grade Description', 'Units',
                    'Transmode', 'Bid Level: Low', 'Bid Level: High', 'Pricing Point', 'Delivery Period', 'Bid']

                elif self.category == 'Grain':
                    data.append(inner_list)

                    columns = ['Week Ending Date','Location','Class','Variety','Grade Description', 'Units',
                    'Transmode', 'Bid Level: Low', 'Bid Level: High', 'Pricing Point', 'Delivery Period']

                else:
                    data.append(inner_list)
                    columns = [th.get_text().encode('utf-8') for tr in table.find_all('tr', attrs={'class':'ReportsTableHeader'})for th in tr.find_all('th')]
        return data, columns

    def generate_df(self, data, columns):
        return pd.DataFrame(data,columns=columns)

    def set_category(self):
        '''
        Method to call the relevant query method/parameters.
        '''

        if self.category == 'Beans, Peas, and Lentils':
            self.beans_query()

        elif self.category == 'Calves':
            self.calves_query()

        elif self.category == 'Cattle':
            self.cattle_query()

        elif self.category == 'Feeder Pigs':
            self.feeder_pigs_query()

        elif self.category == 'Feedstuff`':
            self.feedstuff_query()

        elif self.category == 'Goats':
            self.goats_query()

        elif self.category == 'Grain':
            self.grain_query()

        elif self.category == 'Grain Basis':
            self.cattle_query()

        elif self.category == 'Hay':
            self.hay_query()

        elif self.category == 'Offal and By-products':
            self.offal_query()

        elif self.category == 'Sheep':
            self.sheep_query()


    def make_selection(self,name,value,index=None):
        '''
        Functionalized version of Selenium's Select class.
        Instantiates a Select object and makes selection based on value.
        '''
        selection = Select(self.driver.find_element_by_name(name))
        return selection.select_by_value(value)

    ##############################################################
    #                   COMMODITY QUERY METHODS                  #
    ##############################################################

    def beans_query(self):
        if self.query:
            commod = query['commodity']

            commodity_selection = self.make_selection('commodity', commod)
        else:
            pass


    def calves_query(self):
        if self.query:
            commod = query['commodity']
            subComm = query['subComm']

            commodity_selection = self.make_selection('commodity', commod)
            sub_selection = self.make_selection('subComm', subComm)
        else:
            pass

    def cattle_query(self):
        if self.query:
            commod = self.query['commodity']
            rtype = self.query['rtype']
            subComm = self.query['subComm']

            commodity_selection = self.make_selection('commodity', commod)
            type_selection = self.make_selection('rtype',rtype)
            sub_selection = self.make_selection('subComm', subComm)
        else:
            pass


    def feeder_pigs_query(self):
        if self.query:
            rtype = self.query['rtype']

            commodity_selection = self.make_selection('commodity', commod)
            type_selection = self.make_selection('rtype',rtype)
        else:
            pass

    def feedstuffs_query(self):
        if self.query:
            subComm = self.query['subComm']

            sub_selection = self.make_selection('subComm', subComm)
        else:
            pass

    def goats_query(self):
        if self.query:
            commod = self.query['commodity']
            rtype = self.query['rtype']
            subComm = self.query['subComm']

            commodity_selection = self.make_selection('commodity', commod)
            type_selection = self.make_selection('rtype',rtype)
            sub_selection = self.make_selection('subComm', subComm)
        else:
            pass

    def grain_query(self):
        if self.query:
            organic = self.query['organic']
            commod = self.query['commodity']
            subComm = self.query['subComm']

            organic_selection = self.make_selection('organic', organic)
            commodity_selection = self.make_selection('commodity', commod)
            sub_selection = self.make_selection('subComm', subComm)
        else:
            pass

    def grain_basis_query(self):
        if self.query:
            commod = self.query['commodity']
            rtype = self.query['rtype']
            subComm = self.query['subComm']

            commodity_selection = self.make_selection('commodity', commod)
            type_selection = self.make_selection('rtype',rtype)
            sub_selection = self.make_selection('subComm', subComm)
        else:
            pass

    def hay_query(self):
        if self.query:
            commod = self.query['commodity']

            commodity_selection = self.make_selection('commodity', commod)
        else:
            pass

    def offal_query(self):
        if self.query:
            commod = self.query['commodity']

            commodity_selection = self.make_selection('commodity', commod)
        else:
            pass

    def pork_cuts_query(self):
        pass

    def sheep_query(self):
        if self.query:
            commod = self.query['commodity']
            rtype = self.query['rtype']
            subComm = self.query['subComm']

            commodity_selection = self.make_selection('commodity', commod)
            type_selection = self.make_selection('rtype',rtype)
            sub_selection = self.make_selection('subComm', subComm)
