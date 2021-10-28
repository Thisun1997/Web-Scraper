import scrapy
import json 
import re

class MinisterScrape(scrapy.Spider):
    name = "ministers"
    objects = []
    minister_name = ""
    position = ""
    party = ""
    district = ""
    contact_information = []
    related_subjects = []
    participated_in_parliament = ""
    overall_rank = ""
    biography = ""
    idx = -1

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
            related_subjects_l.append(subject)
          load_more = response.xpath('/html/body/div[2]/div/div/div[1]/div[6]/div/a/@href').get()
        if load_more is not None:
          load_more =  "http://www.manthri.lk/" + load_more
          yield scrapy.Request(load_more, callback=self.details_extractor,cb_kwargs=dict(related_subjects_l = related_subjects_l))
        else:
          self.idx += 1
          self.related_subjects = list(set(related_subjects_l))
          self.minister_name= response.xpath('/html/body/div[2]/section/div/div/div[2]/h1/text()').get().strip().replace("  ", " ")
          p = response.xpath('/html/body/div[2]/section/div/div/div[2]/p/text()').get()
          if p is not None:
            self.position=" , ".join(response.xpath('/html/body/div[2]/section/div/div/div[2]/p/text()').get().strip().split("-"))
          else:
            self.position= "පාර්ලිමේන්තු මන්ත්‍රී"
          self.party = response.xpath('/html/body/div[2]/section/div/div/div[2]/div/p[1]/text()[1]').get().strip().split(",")[0]
          self.district = response.xpath('/html/body/div[2]/section/div/div/div[2]/div/p[1]/a/text()').get().strip()
          contact_l = []
          contact_l.append(response.xpath('/html/body/div[2]/section/div/div/div[2]/div/p[2]/span[1]/text()').get().strip())
          if response.xpath('/html/body/div[2]/section/div/div/div[2]/div/p[2]/span[2]/a/text()').get() is not None:
            contact_l.append(response.xpath('/html/body/div[2]/section/div/div/div[2]/div/p[2]/span[2]/a/text()').get().strip())
          self.contact_information = contact_l

          self.overall_rank= response.xpath('/html/body/div[2]/div/div/div[1]/div[2]/div[1]/span/strong/text()').get().strip()[1:]
          self.participated_in_parliament = response.xpath('/html/body/div[2]/div/div/div[1]/div[2]/div[3]/span/strong/text()').get().strip()

          bio_string = ""
          
          table_personal = response.xpath('/html/body/div[2]/div/div/div[1]/div[8]/table[1]/tbody/tr')
          for i in range(len(table_personal)-1,-1,-1):
            key = table_personal[i].xpath('./td[1]/text()').get().strip()
            value = table_personal[i].xpath('./td[2]/text()').get().strip()
            if key == "ස්ත්‍රී පුරුෂ භාවය:":
              gender = value
              if "හිමි" in self.minister_name:
                pro_noune1 = ""
                pro_noune2 = "උන්වහන්සේ "
              if gender == "පුරුෂ" or gender == "පිරිමි" or gender == "male":
                pro_noune1 = "මහතා"
                pro_noune2 = "මෙතුමා "
              elif gender == "ස්ත්‍රී" or gender == "ගැහැණු" or gender == "female":
                pro_noune1 = "මහත්මිය"
                pro_noune2 = "මෙතුමිය "           
            elif key == "උපන්දිනය:" and value is not None:
              birthday = value
              birthday_string = self.minister_name + " "+ pro_noune1 + " " + birthday + " " + "දින උපත ලබා ඇත." 
              bio_string += birthday_string

          table_edu = response.xpath('/html/body/div[2]/div/div/div[1]/div[8]/table[2]/tbody/tr')
          schools = ""
          edu_string = ""
          for i in range(len(table_edu)):
            key = table_edu[i].xpath('./td[1]/text()').get()
            value = table_edu[i].xpath('./td[2]/text()').get()
            if value is None:
              continue
            else:
              if "පාසැල" in key:
                if edu_string == "": 
                  schools += value
                  edu_string = pro_noune2 + schools + " යන පාසලේ අධ්යාපනය ලබා ඇත."
                else:
                  schools += "; "+value+"; "
                  edu_string = pro_noune2 + schools + " යන පාසල්වල අධ්යාපනය ලබා ඇත."
              elif "ප්‍රථම උපාධිය" in key:
                edu_string += "තම ප්‍රථම උපාධිය "+value+" ලබාගෙන ඇත."
              elif "පශ්චාත් උපාධිය" in key:
                edu_string += " ඊට අමතරව "+ value +" පශ්චාත් උපාධිය ද සම්පූර්ණ කර ඇත."
          
          bio_string += edu_string

          table_party = response.xpath('/html/body/div[2]/div/div/div[1]/div[8]/table[3]/tbody/tr')
          party_string = ""  
          j = "" 
          for i in range(len(table_party)):
            if i>0:
              j = "ද"
              if i == 1:
                party_string+=j+" "
            duration = table_party[i].xpath('./td[1]/text()').get()
            party = table_party[i].xpath('./td[2]').get().split(">")[-2].split(",")[0].strip()
            if duration is not None and party is not None:
              if "සිට" not in duration:
                try:
                  start,end = duration.split(" - ")
                  party_string += start+" සිට "+end+" දක්වා "+party+j
                except:
                  party_string += duration+" පටන්"+party+j
              else:
                party_string += duration+" "+party+j
          party_string += " නියෝජනය කරමින් පාර්ලිමේන්තුවේ අසුන් ගෙන සිටී."

          bio_string += party_string

          self.biography = bio_string

          details= {
              'name' : self.minister_name ,
              'position' : self.position ,
              'party' : self.party ,         
              'district' : self.district ,
              'contact_information' : self.contact_information ,
              'overall_rank' : self.overall_rank ,
              'participated_in_parliament' : self.participated_in_parliament ,
              'related_subjects' : self.related_subjects,
              'biography' : self.biography
              }

          with open("data/"+str(self.idx)+".json", 'w', encoding="utf8") as outfile:
            json.dump([details], outfile,indent = 4,ensure_ascii=False)
          self.objects.append(details)
          
        
    def closed(self, reason):
        with open("data.json", 'w', encoding="utf8") as outfile:
           json.dump(self.objects, outfile,indent = 4,ensure_ascii=False)