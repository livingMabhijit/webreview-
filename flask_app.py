
import requests
from urllib.request import urlopen as req_url
from bs4 import BeautifulSoup as bs
from flask import Flask, render_template, request, jsonify
from flask_pymongo import PyMongo

app = Flask(__name__, template_folder='templates')

app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/admin?authSource=admin'
mongo = PyMongo(app)
#b = dbConn['WebCrawlerDB']  # connecting to the database called crawlerDB

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
        #page_html = page.read()
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
        #detail_rev_list.append(detail_review)
        user_name = item.find_all('p',{'class':'_3LYOAd _3sxSiS'})
        user_name = [i.get_text() for i in user_name]
        #user_name_list.append(user_name)


        # user, rating, review
        page_score = [[u, r, rh, rd] for u, r, rh, rd in zip(user_name, rating, review_head, detail_review)]
        page_prod_review.extend(page_score)

    return page_prod_review



@app.route('/')
def index():
    print("Insid index route....")
    reviews = 1234
    print(f"Reviews = {reviews}")
    if reviews is not None:  # if there is a collection with searched keyword and it has records in it

        #table = db['iphonex']
        # from urllib.request import urlopen as uReq
        flipkart_url = "https://www.flipkart.com/search?q=" + 'iphonex'
        flipkartPage = requests.get(flipkart_url)  # requesting the webpage from the internet
        #flipkartPage = uClient.get()
        #uClient.close()  # closing the connection to the web server
        flipkart_html = bs(flipkartPage.text, "html.parser")  # parsing the webpage as HTML
        products_page = flipkart_html.findAll("div", {"class": "bhgxx2 col-12-12"})  # seacrhing for appropriate tag to redirect to the product link
        del products_page[0:3]  # the first 3 members of the list do not contain relevant information, hence deleting them.
        # box = products_page #  taking the first iteration (for demo)
        prod_links = []
        p_name_list = []
        # {p_name :['user name','rating','review' ]}

        product_rating_details = dict()  # this will hold data for all products

        rating_list = []
        rev_head_list = []
        detail_rev_list = []
        user_name_list = []
        for item in range(0, 5):  # top 5 variants from the list
            box = products_page[item]
            productLink = "https://www.flipkart.com" + box.div.div.div.a[
                'href']  # extracting the actual product link
            prod_links.append(productLink)

        for prod in prod_links[:]:
            product_name = prod.split('/')[3]
            prodRes = requests.get(prod)  # getting the product page from server
            prod_html = bs(prodRes.text, "html.parser")  # parsing the product page as HTML

            all_review_home_page = prod_html.find("div", {"class": "col _39LH-M"})
            all_review_home_page = all_review_home_page.findAll('a')[-1]['href']
            all_review_home_page_url = "https://www.flipkart.com" + all_review_home_page
            all_prod_data = get_all_product_related_info(all_review_home_page_url)
            product_rating_details[product_name] = all_prod_data
            print('Data Processed ------------------')
        #x = table.insert_one(product_rating_details)
        #mongo.db.iphonex.insert(product_rating_details)
        #print(x.inserted_id)
        print("Document inserted!!!")
    #return "Success!!"
    # transform response
    # product_rating_details = [p_data for p_data in product_rating_details.values()][0]
    # product_rating_details = [
    #     {
    #         'Product' : 'apple-iphone-x-space-gray-64-gb',
    #         'Name' : p_data[0],
    #         'Rating' : p_data[1],
    #         'CommentHead': p_data[2],
    #         'Comment' : p_data[3]
    #     }
    #     for p_data in product_rating_details
    # ]
    # return render_template('result.html', reviews=product_rating_details)
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
    return render_template('result.html', reviews=reviews)


if __name__ == "__main__":
    app.run(port=8000,debug=True)