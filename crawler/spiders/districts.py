import scrapy
import json 
import re

class DistrictsScrape(scrapy.Spider):
    name = "districts"
    objects = []
    position = ""
    party = ""
    district = ""
    districts = []
    positions = []
    parties = []
    related_subjects = []
    all_related_subjects = []

    allowed_domains= [
        'manthri.lk'
        ]

    
    def start_requests(self):
        urls = [
          "http://www.manthri.lk/si/politicians",
        ]
        base = "http://www.manthri.lk/si/politicians?page="
        for i in range(2,10):
          urls.append(base+str(i))

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
            print(url)
  
    

    def parse(self, response):

        for quote in response.xpath('/html/body/div[2]/div/div[1]/ul[1]/li/h4/a/@href').getall():
            quote = "http://www.manthri.lk/"+quote
            related_subjects_l = []
            yield scrapy.Request(quote, callback=self.details_extractor,cb_kwargs=dict(related_subjects_l = related_subjects_l))
            
    def details_extractor(self, response, related_subjects_l):
        t = response.xpath('/html/body/div[2]/div/div/div[1]/div[6]/table')
        if len(t) == 0:
          related_subjects_l = []
          load_more = None
        else:
          table = response.xpath('/html/body/div[2]/div/div/div[1]/div[6]/table')[0]
          for subject in table.xpath('//tbody/tr/td[3]/ul/li/a/text()').getall():
            related_subjects_l += subject.split()
          load_more = response.xpath('/html/body/div[2]/div/div/div[1]/div[6]/div/a/@href').get()
        if load_more is not None:
          load_more =  "http://www.manthri.lk/" + load_more
          yield scrapy.Request(load_more, callback=self.details_extractor,cb_kwargs=dict(related_subjects_l = related_subjects_l))
        else:
          self.related_subjects = list(set(related_subjects_l))
          self.district = response.xpath('/html/body/div[2]/section/div/div/div[2]/div/p[1]/a/text()').get().strip()
          p = response.xpath('/html/body/div[2]/section/div/div/div[2]/p/text()').get()
          if p is not None:
            self.position=",".join(response.xpath('/html/body/div[2]/section/div/div/div[2]/p/text()').get().strip().split("-"))
          else:
            self.position= "පාර්ලිමේන්තු මන්ත්‍රී"
          self.party = response.xpath('/html/body/div[2]/section/div/div/div[2]/div/p[1]/text()[1]').get().strip().split(",")[0]
          
          self.all_related_subjects += self.related_subjects
          self.districts += self.district.split()
          self.positions.append(self.position)
          self.parties += self.party.split()

          
        
    def closed(self, reason):
        self.all_related_subjects = list(set(self.all_related_subjects))
        self.districts = list(set(self.districts))
        self.positions = list(set([ p.split(",")[0] for p in self.positions]))
        self.parties = list(set(self.parties))
        self.objects = {
          "districts" : self.districts,
          "positions" : self.positions,
          "parties" : self.parties,
          "realated_sub" : self.all_related_subjects
        }
        with open("details.json", 'w', encoding="utf8") as outfile:
           json.dump(self.objects, outfile,indent = 4,ensure_ascii=False)
        






