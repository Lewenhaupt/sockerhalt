import psycopg2

from db_config import db_config


def create_tables():
    """ create tables in the PostgreSQL database"""
    commands = (
        """
        CREATE TABLE products (
            product_id VARCHAR(255) PRIMARY KEY,
            product JSON NOT NULL
        )
        """,
        """ 
        CREATE TABLE sitemap_last_updated (
            sitemap VARCHAR(255) PRIMARY KEY,
            last_updated VARCHAR(255) NOT NULL
        )
        """
    )
    conn = None
    try:
        config = db_config()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        cur.close()
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    create_tables()
