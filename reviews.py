#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Written as part of https://www.scrapehero.com/how-to-scrape-amazon-product-reviews-using-python/
from lxml import html
from json import dump,loads
from requests import get
import matplotlib.pyplot as plt
from re import sub
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from dateutil import parser as dateparser
from time import sleep
import numpy as np
import json

def get_sentiments(text):
    analyzer = SentimentIntensityAnalyzer()
    print(text)
    print(analyzer.polarity_scores(text))
    return analyzer.polarity_scores(text)

def ParseReviews(amazon_url):
   
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}
    for i in range(5):
        response = get(amazon_url, headers = headers, verify=False, timeout=30)
        if response.status_code == 404:
            return {"url": amazon_url, "error": "page not found"}
        if response.status_code != 200:
            continue
        
        cleaned_response = response.text.replace('\x00', '')
        
        parser = html.fromstring(cleaned_response)
        REVIEW_SECTION_1 = '//div[contains(@id,"reviews-summary")]'
        REVIEW_SECTION_2 = '//div[@data-hook="review"]'

        procduct_reviews = parser.xpath(REVIEW_SECTION_1)

        if not procduct_reviews:
            procduct_reviews = parser.xpath(REVIEW_SECTION_2)
       
        reviews_list = []
        
        for review in procduct_reviews:
            XPATH_RATING  = './/i[@data-hook="review-star-rating"]//text()'
            XPATH_REVIEW_HEADER = './/a[@data-hook="review-title"]//text()'
            XPATH_REVIEW_POSTED_DATE = './/span[@data-hook="review-date"]//text()'
            XPATH_REVIEW_TEXT_1 = './/div[@data-hook="review-collapsed"]//text()'
            XPATH_REVIEW_TEXT_2 = './/div//span[@data-action="columnbalancing-showfullreview"]/@data-columnbalancing-showfullreview'
            XPATH_REVIEW_COMMENTS = './/span[@data-hook="review-comment"]//text()'
            XPATH_AUTHOR = './/span[contains(@class,"profile-name")]//text()'
            XPATH_REVIEW_TEXT_3 = './/div[contains(@id,"dpReviews")]/div/text()'
            
            raw_review_author = review.xpath(XPATH_AUTHOR)
            raw_review_rating = review.xpath(XPATH_RATING)
            raw_review_header = review.xpath(XPATH_REVIEW_HEADER)
            raw_review_posted_date = review.xpath(XPATH_REVIEW_POSTED_DATE)
            raw_review_text1 = review.xpath(XPATH_REVIEW_TEXT_1)
            raw_review_text2 = review.xpath(XPATH_REVIEW_TEXT_2)
            raw_review_text3 = review.xpath(XPATH_REVIEW_TEXT_3)

            # Cleaning data
            author = ' '.join(' '.join(raw_review_author).split())
            review_rating = ''.join(raw_review_rating).replace('out of 5 stars', '')
            review_header = ' '.join(' '.join(raw_review_header).split())

            try:
                review_posted_date = dateparser.parse(''.join(raw_review_posted_date)).strftime('%d %b %Y')
            except:
                review_posted_date = None
            review_text = ' '.join(' '.join(raw_review_text1).split())

            # Grabbing hidden comments if present
            if raw_review_text2:
                json_loaded_review_data = loads(raw_review_text2[0])
                json_loaded_review_data_text = json_loaded_review_data['rest']
                cleaned_json_loaded_review_data_text = re.sub('<.*?>', '', json_loaded_review_data_text)
                full_review_text = review_text+cleaned_json_loaded_review_data_text
            else:
                full_review_text = review_text
            if not raw_review_text1:
                full_review_text = ' '.join(' '.join(raw_review_text3).split())

            raw_review_comments = review.xpath(XPATH_REVIEW_COMMENTS)
            review_comments = ''.join(raw_review_comments)
            review_comments = sub('[A-Za-z]', '', review_comments).strip()
            review_dict = {
                                'review_comment_count': review_comments,
                                'review_text': full_review_text,
                                'review_posted_date': review_posted_date,
                                'review_header': review_header,
                                'review_rating': review_rating,
                                'review_author': author

                            }
            reviews_list.append(review_dict)

        data = {
                   # 'ratings': ratings_dict,
                    'reviews': reviews_list,
                    'url': amazon_url,
                   # 'name': product_name,
                   # 'price': product_price
                
                }
        return data

    return {"error": "failed to process the page", "url": amazon_url}
            

AmazonProductList = ['https://www.amazon.com/All-Day-Luminous-Weightless-Foundation/dp/B00T45UQSI/ref=sr_1_3?keywords=Nars%2Bfoundation%2Bfor%2Bwomen&qid=1561860534&s=gateway&sr=8-3&th=1',
            'https://www.amazon.com/MAC-Studio-Fluid-Foundation-SPF15/dp/B007ANN0CA/ref=sr_1_10?crid=2HMBR7964RZZC&keywords=mac+foundation+women&qid=1561858886&s=gateway&sprefix=mac+foundation+for+women%2Caps%2C248&sr=8-10',
            'https://www.amazon.com/COVERGIRL-CGRMQ0347-Simply-Ageless-Foundation/dp/B0026P3GX0/ref=sr_1_48_sspa?keywords=olay%2Bfoundation%2Bfor%2Bwomen&qid=1561859200&s=gateway&sr=8-48-spons&th=1']
            
extracted_data = []
for asin in AmazonProductList:
    print("Downloading and processing page http://www.amazon.com/dp/" + asin)
    extracted_data.append(ParseReviews(asin))
    sleep(5)
f = open('data.json', 'w')
dump(extracted_data, f, indent=4) 

#with open('data.json') as json_file:  
#    extracted_data = json.load(json_file) 
    
Positive=[]
Negative=[]
reviewPos=[]
for reviewData in extracted_data:
    
    sentiments1 = [get_sentiments(comment["review_text"]) for comment in reviewData["reviews"]]


    Review1pos = [sent['pos'] for sent in sentiments1]
    reviewPos.append(Review1pos)
    Review1neg = [sent['neg'] for sent in sentiments1]
    Positive.append(sum(Review1pos)/len(Review1pos))
    Negative.append(sum(Review1neg)/len(Review1neg))

fig = plt.figure()
axes = fig.add_subplot(111)
n=3
index=np.arange(n)
barwidth=0.45
opacity=0.8


objects=('NARS','CoverGirl','MAC')

product1 = plt.bar(index, Positive, barwidth,
alpha=opacity,
color='c',
label='Positive')

product2 = plt.bar(index + barwidth, Negative,barwidth,
alpha=opacity,
color='r',
label='Negative')


plt.xticks(index, objects)
plt.ylabel('Mean of Sentiments of Reviews')
plt.title('Sentiment Analysis of Customer Reviews')

plt.legend()
plt.tight_layout()

plt.show()

    

    
    
    
