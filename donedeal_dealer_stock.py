import requests
import bs4
import time
import xlsxwriter
import datetime

# this function generates a dictionary of dealers and their href.
def dealer_dictionary_generator(county):

	dealer_count = 0
	dealer_dictionary={}

	# requests url and stores webpage as soup var
	url = "https://www.donedeal.ie/find-a-dealer?counties="+county
	headers={'User-Agent':'Mozilla/5'}

	page = requests.get(url, headers = headers)
	soup = bs4.BeautifulSoup(page.content,'lxml').find("div", id="js-dealer-directory")

	# this variable stores the total number of dealers in the county selected
	dealer_number = int(soup.find("h1", class_="info-title").text.split("of ",1)[1])

	#  dealer number + 10 as there are 10 dealers per web page on DoneDeal.
	while dealer_count <= dealer_number+10:
		url = 'https://www.donedeal.ie/find-a-dealer?from='+str(dealer_count)+'&counties='+county
		page = requests.get(url, headers = headers)
		time.sleep(2)
		soup = bs4.BeautifulSoup(page.content,'lxml').find("div", id="js-dealer-directory")

		# iterate through all dealers on web page and update dictionary.
		for x in soup.find_all("div", class_="motordealer-card"):
			dealer_name = x.find("span", itemprop="name").text
			dealer_href = x.find('a')['href']
			dealer_dictionary.update( {dealer_name : dealer_href} )

		dealer_count +=10

	return dealer_dictionary

# this function generates the spreadsheet of all dealer stock for selected county.
def spreadsheet_generator(dealer_dictionary,county):

	# the below lines deal with the naming and the formatting of the spreadsheet
	date = datetime.datetime.now().strftime("%d") + datetime.datetime.now().strftime("%m") + datetime.datetime.now().strftime("%y")

	workbook = xlsxwriter.Workbook('donedeal_stock_'+county.lower()+'_'+date+'.xlsx') 
	worksheet = workbook.add_worksheet("Units Info")
	bold = workbook.add_format({'bold': True})
	currency_format = workbook.add_format({'num_format': '#,##0'})

	# tab 1 has stock information
	worksheet.write("A1", "Dealer Name",bold)
	worksheet.write("B1", "Year",bold)
	worksheet.write("C1", "Model",bold)
	worksheet.write("D1", "Type",bold)
	worksheet.write("E1", "Mileage",bold)
	worksheet.write("F1", "Price",bold)
	worksheet.write("G1", "Last update",bold)
	worksheet.write("H1", "Ad Link",bold)
	worksheet.write("I1", "Ad ID",bold)
	row = 1

	# tab 2 has dealer information
	worksheet1 = workbook.add_worksheet("Dealer Info")
	worksheet1.write("A1", "Dealer Name",bold)
	worksheet1.write("B1", "Units",bold)
	worksheet1.write("C1", "Total Value",bold)
	worksheet1.write("D1", "Avg Value",bold)
	row1 = 1

	# iterate through dealer dictionary
	for k,v in dealer_dictionary.items():

		# stores total value of stock for tab 2 in spreadsheet.
		total_price = 0

		# requests url of indivdual dealer and stores in soup var
		url = "https://www.donedeal.ie"+v
		headers={'User-Agent':'Mozilla/5'}
		page = requests.get(url, headers = headers)
		soup = bs4.BeautifulSoup(page.content,'lxml').find("div", id="js-dealer-showroom-panel-main")

		# try / except as some dealers may not have any live ads so try extract ad info and if they do not exist go to except.
		try:
			# if dealer has no ads this will trigger exception straight away as trying to convert string to int.
			number_ads = int(soup.find("h2", id="our-stock").text.split(" ",1)[0])

			# write dealer name to tab2
			worksheet1.write(row1, 0, k)
			
			ad_count = 0

			# number_ads + 30 as that's how many ads are on a webpage
			while ad_count <= number_ads+30:
				url = "https://www.donedeal.ie"+v+"?start="+str(ad_count)
				page = requests.get(url, headers = headers)
				time.sleep(2)
				soup = bs4.BeautifulSoup(page.content,'lxml').find("div", id="js-dealer-showroom-panel-main")

				# extract all relevant ad information and update both spreadsheet tabs
				for x in soup.find("ul", class_="card-collection").find_all('li', class_='card-item'):
					information = x.find("div", class_="card").find("ul", class_="card__body-keyinfo").find_all('li')
					try:
						year = int(information[0].text)
					except:
						year = "undefined"
					counter = sum(1 for ul in information for li in ul)
					# set milage to zero in case value not in list items. All others should be there.
					mileage = 0
					# iterate through list items and if below values contained update variables. All should be there so only mileage has an error check.
					for i in range(counter):
						if "Diesel" in information[i].text or "Petrol" in information[i].text:
							model_type = information[i].text.strip()
						if "hours" in information[i].text or "days" in information[i].text or "day" in information[i].text:
							last_update = information[i].text.strip()
						if "mi" in information[i].text or "km" in information[i].text:
							mileage = information[i].text.strip()

					model = x.find("div", class_="card").find('p', class_= 'card__body-title').text.strip()
					# price will either be an int so try that or 'no price' string so that's except message.
					try:
						price = int(x.find("div", class_="card").find('p', class_= 'card__price').text.replace(",","").replace("",""))
						total_price += price
					except:
						price = x.find("div", class_="card").find('p', class_= 'card__price').text.strip()
					ad_href = x.find('a')['href'].strip()
					ad_ID = int(x['id'].split("cad-card-",1)[1])

					# write variables to excel row in tab1.
					worksheet.write(row, 0, k)
					worksheet.write(row, 1, year)
					worksheet.write(row, 2, model)
					worksheet.write(row, 3, model_type)
					worksheet.write(row, 4, mileage)
					worksheet.write(row, 5, price,currency_format)
					worksheet.write(row, 6, last_update)
					worksheet.write(row, 7, ad_href)
					worksheet.write(row, 8, ad_ID)
					row += 1

				ad_count +=30

			# write variables to excel row in tab2.
			worksheet1.write(row1, 1, number_ads)
			worksheet1.write(row1, 2, int(total_price),currency_format)
			worksheet1.write(row1, 3, int(total_price/number_ads),currency_format)
			row1 += 1

		except: 
			# if no ads for dealer this except triggered so just write to tab2 this information. 
			# write variables to excel row in tab2.
			worksheet1.write(row1, 0, k)
			worksheet1.write(row1, 1, 0)
			worksheet1.write(row1, 2, 0,currency_format)
			worksheet1.write(row1, 3, 0,currency_format)
			row1 += 1

	workbook.close()

	print ("Report has now finished and is saved in the script folder.")

# counties list to check if input from user is actually valid.
counties = ["carlow","cavan","clare","cork","donegal","dublin","galway","kerry","kildare","kilkenny","laois","leitrim","limerick","longford","louth","mayo","meath","monaghan","offaly","roscommon","sligo","tipperary","waterford","westmeath","wexford","wicklow"]

county = input("Please enter a county:")

if county.lower() in counties:
	print("Script now running. Message will print when spreadsheet complete.")
	dealers = dealer_dictionary_generator(county.capitalize())
	spreadsheet = spreadsheet_generator(dealers,county.capitalize())
else:
	print("County not valid")