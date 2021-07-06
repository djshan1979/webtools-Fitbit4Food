# file for CURD operation 
import sqlite3

class DbController():
	# create db id not exist
	def __init__(self, db_name = 'dynamic_database.db'):
		self.conn = None
		try:
			self.conn = sqlite3.connect(db_name)
			self.cursor = self.conn.cursor()
		except Exception as e:
			#print(e)
			pass
		else:
			if self.conn != None:
				product_sql = '''CREATE TABLE IF NOT EXISTS product_data(
					URL NOT NULL UNIQUE,
					'ProductTitle' CHAR(200),tag CHAR(100),
					'ProductPrice' REAL,'Product Volume' CHAR(20),'price per base volume' REAL,
					Category CHAR(100),
					'ProductDetail' CHAR(1000),Ingredients CHAR(1000),
					Nutritional_information CHAR(1000),
					'Allergenwarnings' CHAR(1000),
					Claims CHAR(1000),
					Endorsements CHAR(1000),
					'ProductImage' CHAR(500),
					'Productorigin' CHAR(100),
					'RL_weights' REAL DEFAULT 0
				)'''
				self.cursor.execute(product_sql)
				# print("Table created successfully........")

				# Commit your changes in the database
				self.conn.commit()

				#Closing the connection
				#self.conn.close()

	# Upgrade product weight
	def reward_product(self, list_of_tuple):
		try:
			self.cursor.execute("INSERT OR IGNORE INTO product_data(URL,'ProductTitle',tag,'ProductPrice','ProductVolume','priceperbasevolume',Category,'ProductDetail',Ingredients,Nutritional_information,'Allergenwarnings',Claims,Endorsements,'ProductImage','Productorigin') VALUES(?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?) ON CONFLICT(URL) DO UPDATE SET RL_weights =  RL_weights + 1;",list_of_tuple)
			# Commit your changes in the database
			self.conn.commit()
			return True

		except Exception as exp:
			# Rolling back in case of error
			self.conn.rollback()
			print(exp)
			return False

	# downgrade product weight
	def feedback_product(self, list_of_tuple):
		try:
			self.cursor.execute("INSERT OR IGNORE INTO product_data(URL,'ProductTitle',tag,'ProductPrice','ProductVolume','priceperbasevolume',Category,'ProductDetail',Ingredients,Nutritional_information,'Allergenwarnings',Claims,Endorsements,'ProductImage','Productorigin') VALUES(?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?) ON CONFLICT(URL) DO UPDATE SET RL_weights =  RL_weights - 1;",list_of_tuple)
			# Commit your changes in the database
			self.conn.commit()
			return True
		except Exception as exp:
			# Rolling back in case of error
			self.conn.rollback()
			print(exp)
			return False


if __name__ == "__main__":
	d1 = DbController("dynamic_database.db")
	list_of_tuple = ("link"," "," "," "," "," ","","","","","","","","","")
	print("HERE")
	# d1.reward_product(list_of_tuple)
	d1.feedback_product(list_of_tuple)
