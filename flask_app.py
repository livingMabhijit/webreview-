import pymongo
import requests
# from urllib.request import urlopen as req_url
from bs4 import BeautifulSoup as bs
from flask import Flask, render_template, request, jsonify
# from flask_pymongo import PyMongo


app = Flask(__name__, template_folder='templates')

def get_all_product_related_info(review_home_url):
    all_reviews = []
    resp = requests.get(review_home_url)
    total_page_count = bs(resp.text, 'html.parser')
    total_page_count = total_page_count.find("div",{'class':'_2zg3yZ _3KSYCY'})
    page_num= total_page_count.span.get_text().split()[3]
    page_num = int(''.join([x for x in page_num if x != ',']))
    all_reviews += web_data(review_home_url)
    for page in range(2, page_num+1):
        all_reviews += web_data(review_home_url, page)
    return all_reviews
def web_data(pg_url, pg_num=None):
    try:
        if pg_num is None:
            url = pg_url
        else:
            url = pg_url+'&page='+str(pg_num)
        page = requests.get(url)
        page_soup = bs(page.text,'html.parser')
    #     page.close()
        all_reviews = page_soup.findAll("div",{'class':'_1PBCrt'})

        page_prod_review = []
    except:
        return 'Something went wrong in product details page'


    for item in all_reviews:
        rating = item.find_all('div',{'class':'hGSR34 E_uFuv'})
        rating = [i.get_text() for i in rating]
        #rating_list.append(rating)
        review_head = item.find_all('p',{'class':'_2xg6Ul'})
        review_head = [i.get_text() for i in review_head]
        #rev_head_list.append(review_head)
        detail_review = item.find_all('div',{'class':'qwjRop'})
        detail_review = [i.get_text() for i in detail_review]
        detail_review = [i.strip('READ MORE') for i in detail_review]
        user_name = item.find_all('p',{'class':'_3LYOAd _3sxSiS'})
        user_name = [i.get_text() for i in user_name]
        # user, rating, review
        page_score = [[u, r, rh, rd] for u, r, rh, rd in zip(user_name, rating, review_head, detail_review)]
        page_prod_review.extend(page_score)
    return page_prod_review

@app.route('/',methods=['POST','GET'])
def index():
    print("Insid index route....")
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "")
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")
            db = dbConn['ReviewCrawlerDB']
            reviews = db[searchString]
            reviews = reviews.find()
            if reviews.count() > 0:
                rev_dict = dict()
                for row in reviews:
                    rev_dict.update(row)
                del rev_dict['_id']
                # print(rev_dict)
                cached_reviews = list()
                for key, val in rev_dict.items():
                    # key = " ".join([word.capitalize() for word in key.split('-')])
                    for r in val:
                        cached_reviews.append({
                            'Product': key,
                            'Name': r[0],
                            'Rating': r[1],
                            'CommentHead': r[2],
                            'Comment': r[3]
                        })
                print(cached_reviews)
                print("executing if .........")
                return render_template('result.html', reviews=cached_reviews)
            else:
                print("executing else.....")
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString#'iphonex'
                flipkartPage = requests.get(flipkart_url)  # requesting the webpage from the internet
                flipkart_html = bs(flipkartPage.text, "html.parser")  # parsing the webpage as HTML
                products_page = flipkart_html.findAll("div", {"class": "bhgxx2 col-12-12"})  # seacrhing for appropriate tag to redirect to the product link
                del products_page[0:3]  # the first 3 members of the list do not contain relevant information, hence deleting them.
                prod_links = []
                p_name_list = []

                product_rating_details = dict()  # this will hold data for all products
                table = db[searchString]
                rating_list = []
                rev_head_list = []
                detail_rev_list = []
                user_name_list = []
                for item in range(0, 5):  # top 5 variants from the list
                    box = products_page[item]
                    productLink = "https://www.flipkart.com" + box.div.div.div.a['href']  # extracting the actual product link
                    prod_links.append(productLink)

                for prod in prod_links[:1]:
                    product_name = prod.split('/')[3]
                    prodRes = requests.get(prod)  # getting the product page from server
                    prod_html = bs(prodRes.text, "html.parser")  # parsing the product page as HTML

                    all_review_home_page = prod_html.find("div", {"class": "col _39LH-M"})
                    all_review_home_page = all_review_home_page.findAll('a')[-1]['href']
                    all_review_home_page_url = "https://www.flipkart.com" + all_review_home_page
                    all_prod_data = get_all_product_related_info(all_review_home_page_url)
                    product_rating_details[product_name] = all_prod_data
                    print('Data Processed ------------------')

                # mongo.db.iphonex.insert(product_rating_details
                reviews = []
                for key, val in product_rating_details.items():
                    for row in val:
                        reviews.append({
                            'Product' : key,
                            'Name' : row[0],
                            'Rating' : row[1],
                            'CommentHead': row[2],
                            'Comment' : row[3]
                        })
                # reviews.append(product_rating_details)
            x = table.insert_one(product_rating_details)
            print(x.inserted_id)
            print("Document inserted!!!")
            return render_template('result.html', reviews=reviews)

        except Exception as e:
            reviews = []
            return render_template('index.html')
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(port=7800,debug=True)
