from usda_selenium import USDAscrape

organic_query = {'organic':'Yes','commodity':'Feedstuff','subComm':'Soybean Meal High'}
organic = USDAscrape('Grain', '01/02/2010','02/25/2017',query=organic_query)
organic.selenium_session()

cattle_query = {'commodity': 'Feeder', 'rtype':'wavg', 'subComm':'Steers'}
cattle = USDAscrape('Cattle','02/22/2017','02/27/2017',query=cattle_query)
cattle.selenium_session()
