import psycopg2
import db_tables
from db_config import db_config
import requests


def prepare():
    db_tables.create_tables()


def download_sitemap_list():
    URL = "https://www.systembolaget.se/sitemap-produkter.xml"

    response = requests.get(URL)
    with open('tmp/sitemaps.xml', 'wb') as file:
        file.write(response.content)


def parse_sitemap_list():
    import xml.etree.ElementTree as ET

    product_tree = ET.parse('tmp/sitemaps.xml')
    root = product_tree.getroot()

    conn, cur = create_db_connection()

    insert_command = """
            INSERT INTO sitemap_last_updated VALUES 
            (%s, %s)
            ON CONFLICT ON CONSTRAINT sitemap_last_updated_pkey
            DO 
                UPDATE SET last_updated = EXCLUDED.last_updated;
        """

    for sitemap_xml in root:
        sitemap = sitemap_xml[0].text
        last_updated = sitemap_xml[1].text
        print('handling sitemap', sitemap)
        if is_sitemap_updated(sitemap, last_updated):
            cur.execute(insert_command, (sitemap, last_updated))
            download_sitemap(sitemap)
            download_products(sitemap)

    conn.commit()
    cur.close()


def create_db_connection():
    config = db_config()
    conn = psycopg2.connect(**config)
    cur = conn.cursor()
    return conn, cur


def download_sitemap(sitemap):
    name = sitemap_filename(sitemap)
    response = requests.get(sitemap)
    with open('tmp/' + name, 'wb') as file:
        file.write(response.content)


def sitemap_filename(sitemap):
    name = sitemap.split('.se/', 1)[1]
    return name


def is_sitemap_updated(s, updated):
    print('checking if sitemap %s is updated' % s)
    sql = """
        SELECT last_updated from sitemap_last_updated
        WHERE sitemap = %s
    """
    conn, cur = create_db_connection()
    cur.execute(sql, [s])
    last_updated = cur.fetchone()
    cur.close()
    return last_updated != updated


def download_products(sitemap):
    import xml.etree.ElementTree as ET
    name = sitemap_filename(sitemap)
    product_tree = ET.parse('tmp/' + name)
    root = product_tree.getroot()

    conn, cur = create_db_connection()

    for product_url in root:
        product_url = product_url[0].text
        download_product(product_url=product_url, connection=conn, cursor=cur)


def download_product(product_url, connection, cursor):
    from bs4 import BeautifulSoup
    import json

    sql = """
        INSERT INTO products VALUES 
        (%s, %s)
         ON CONFLICT ON CONSTRAINT products_pkey
            DO 
                UPDATE SET product = EXCLUDED.product;
    """

    split = product_url.split('/')
    product_id = 'unknown'
    if split[-1] != '':
        product_id = split[-1]
    else:
        product_id = split[-2]
    print(product_id)
    response = requests.get(product_url)
    if response.status_code == 200:
        product_page = response.content
        parsed = BeautifulSoup(product_page, features="html.parser")
        product_details = parsed.find('div', attrs={'data-react-component': 'ProductDetailPageContainer'}).get('data-props')
        product_details = json.loads(product_details)
        # print(json.dumps(product_details['product'], indent=4, sort_keys=True))
        cursor.execute(sql, (product_id, json.dumps(product_details)))
        connection.commit()
    else:
        print('failed to retrieve product from %s' % product_url)

# conn = psycopg2.connect("dbname=products user=postgres password=admin host=localhost")
# cur = conn.cursor()

if __name__ == '__main__':
    prepare()
    download_sitemap_list()
    parse_sitemap_list()
    # conn, cur = create_db_connection()
    # download_product('https://www.systembolaget.se/produkt/cider-blanddrycker/garage-hard-lemon-8886503/',
    #                  conn, cur)
