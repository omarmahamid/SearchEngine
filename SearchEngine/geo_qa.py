# omarmahamid : 207705377
# Ansigbaria : 314786476

import lxml.html
import rdflib
import requests
import sys

wiki_prefix = "http://en.wikipedia.org"
Countries_URL = "https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)"

def extract_charecter_information(url):
	res = requests.get(url)
	if res.status_code != 200:
		return ""
	doc = lxml.html.fromstring(res.content)
	infobox = doc.xpath("//table[contains(@class, 'infobox')]")[0]

	birth_date = ""
	b = infobox.xpath("//table//th[contains(text(), 'Born')]")
	if b != []:
		lst = b[0].xpath("./../td//span[@class='bday']//text()")
		if lst != []:
			birth_date = lst[0].replace(" ", "_")

	return birth_date



def extract_countries_information(url):
	res = requests.get(url) 
	doc = lxml.html.fromstring(res.content)
	
	table = doc.xpath("//table[contains(@id, 'main')]")[0]
	countries = table.xpath("//td//span/a[@title]/@href")

	president = prime_minister = population = area = government = capital = ""
	bdate2 = bdate1 = ""

	with open("ontology.nt", 'a+') as writer:
		for c in countries:
			president = prime_minister = population = government = capital = ""
			bdate2 = bdate1 = ""

			page = requests.get(wiki_prefix + c)
			document = lxml.html.fromstring(page.content)
			infobox = document.xpath("//table[contains(@class, 'infobox')]")[0]

			country_name = c[6:]

			president_h = infobox.xpath("//th//div/a[text()='President']")
			if president_h != []:
				president = president_h[0].xpath("../../../td//a/text()")[0].replace(" ", "_")
				link = president_h[0].xpath("../../../td//a/@href")[0]
				bdate2 = extract_charecter_information(wiki_prefix + link)

			prime_minister_h = infobox.xpath("//table//th[contains(text(), 'Prime Minister')]")
			if prime_minister_h != []:
				prime_minister = prime_minister_h[0].xpath("./../td/text()")[0].areplace(" ", "_")
				link = prime_minister_h[0].xpath("./../td//a/@href")[0]
				bdate1 = extract_charecter_information(wiki_prefix +link)


			population_h = infobox.xpath("//table//th//a[text()='Population']")
			if population_h != []:
				estimate = population_h[0].xpath("../../..//text()[contains(., 'estimate') or contains(., 'census') or contains(., 'Estimate')]/..")[0]
				lst = estimate.xpath("../..//td[1]//text()")
				if '\n' in lst:
					lst.remove('\n')
				population = lst[0].replace(" ", "")
				if population[-1] == '(':
					population = population.replace('(', '')
				if population[-1] == '\t':
					population = population.replace('\t', '')
				if population[-1] == '\n':
					population = population.replace('\n', '')
				d=0
				for ch in population[::-1]:
					if ch < '0' or ch > '9':
						d += 1
					else:
						break
				population = population[:-d] if d != 0 else population
				if '(' in population:
					population = population[:population.index('(')]


			government_h = infobox.xpath("//table//tr/th[.//text()='Government']//text()/..")
			if government_h != []:
				elements = government_h[0].xpath("./../../td//text()")
				if elements == []:
					elements = government_h[0].xpath(".//../td//text()")
				for elem in elements:
					if 'de facto' in elem:
						break
					if '(' in elem or '\n' in elem:
						continue
					government += elem.replace(" ", "_") + "_"
				government = government[:-1]
				if u'\xa0' in government:
					government = government.replace(u'\xa0', u' ')
				if ' ' in government:
					government = government.replace(' ', '')
				if '___' in government:
					government = government.replace('___', '_')
				if '__' in government:
					government = government.replace('__', '_')


			capital_h = infobox.xpath("//table//th[contains(text(), 'Capital')]")
			if capital_h != []:
				capital_lst = capital_h[0].xpath("./../td//text()")
				if '\n' in capital_lst:
					capital_lst.remove('\n')
				capital = capital_lst[0].replace(" ", "_")


			if president:
				writer.write(u"<http://example.org/{0}> <http://example.org/president> <http://example.org/{1}> .\n".format(country_name, president).encode('utf-8'))
			if prime_minister:
				writer.write("<http://example.org/{0}> <http://example.org/prime_minister> <http://example.org/{1}> .\n".format(country_name, prime_minister).encode('utf-8'))
			writer.write(u"<http://example.org/{0}> <http://example.org/population> <http://example.org/{1}> .\n".format(country_name, population).encode('utf-8'))
			if government:
				writer.write(u"<http://example.org/{0}> <http://example.org/government> <http://example.org/{1}> .\n".format(country_name, government).encode('utf-8'))
			if capital:
				writer.write(u"<http://example.org/{0}> <http://example.org/capital> <http://example.org/{1}> .\n".format(country_name, capital).encode('utf-8'))
			if bdate2:
				writer.write(u"<http://example.org/{0}> <http://example.org/born> <http://example.org/{1}> .\n".format(president, bdate2).encode('utf-8'))
			if bdate1:
				writer.write(u"<http://example.org/{0}> <http://example.org/born> <http://example.org/{1}> . \n".format(prime_minister, bdate1).encode('utf-8'))



# this function get a natural language(English) question
# decode the given question and return an appropriate answer
def decode_and_extract_data(question):
	answer = ""
	graph = rdflib.Graph()
	graph.parse("ontology.nt", format="nt")
	# What Questions
	# cehck if what word in the question and then according to the question in pdf 
	if 'What' in question:
		index1 = question.index('the ')+4
		index2 = question.index(' of ')
		r = question[index1:index2].replace(' ', '_')
		e = question[index2+4:-1].replace(' ', '_')
		answer = list(graph.query("select ?x where { <http://example.org/%s> <http://example.org/%s> ?x } " % (e,r)))[0][0][19:]
	elif 'When' in question:
		index1 = question.index('the ')+4
		index2 = question.index(' of ')
		r = question[index1:index2].replace(' ', '_')
		e = question[index2+4:-6].replace(' ', '_')
		answer = list(graph.query("select ?date where { <http://example.org/%s> <http://example.org/%s> ?x . ?x <http://example.org/born> ?date } " % (e,r)))[0][0][19:]
	else:
		# Who Questions
		if ' of ' in question:
			index1 = question.index('the ')+4
			index2 = question.index(' of ')
			r = question[index1:index2].replace(' ', '_')
			e = question[index2+4:-1].replace(' ', '_')
			answer = list(graph.query("select ?x where { <http://example.org/%s> <http://example.org/%s> ?x } " % (e,r)))[0][0][19:].replace('_', ' ')
		else:
			index = question.index("Who is ")+7
			name = question[index:-1].replace(' ', '_')
			answer = list(graph.query("select ?x where { ?x <http://example.org/president> <http://example.org/%s> } " % name ))[0][0]
			if answer == "":
				answer = 'Prime Minister of ' + list(graph.query("select ?x where { ?x <http://example.org/prime_minister> <http://example.org/%s> } " % name))[0][0][19:].replace('_', ' ')
			else:
				answer = "President of " + answer[19:].replace('_', ' ')
	return answer



# The programm assume that all of the question according to pdf question , otherwise there is a bug.
if __name__ == '__main__':
	if len(sys.argv)!=3:
		print("There is an Error in input , Check accoding to Instructions")
	else:
		# check if the function is create and the word after that is ontology.nt
		if sys.argv[1] == 'create':
			if sys.argv[2] == 'ontology.nt':
				extract_countries_information(Countries_URL)
				print("Success Ontology Building")
			else:
				print("You have to input this Format :: python geo_qa.py create ontology.nt")
		# check if the function is question , then Decode the question and Extract Data
		if sys.argv[1] == 'question':
			answer = decode_and_extract_data(sys.argv[2])
			print(answer)
