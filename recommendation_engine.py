##############################################################################################

# This file contain NLP based recommendation engine
# Class Recommendation_Engine can easily separable for future use. 
# Main method is available below to play with key words

##############################################################################################

import nltk
import string # to process standard python strings
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
import time
import inflect
import sqlite3
import pandas as pd

class Recommendation_Engine:
    def __init__(self, my_preference):

        # read data from csv
        self._read_csv("all_product_data.csv")

        self.get_dynamic_data('dynamic_database.db')

        # select relevent features
        self.feature_selection()

        # data pre process
        self.data_pre_processing()

        # initialize of tokanization and vectorization
        self.tokanization()

        self.init_vectorization(my_preference)

        # Initialize inflect engine
        self.inflect_engine = inflect.engine()

    def get_dynamic_data(self, dbname = 'dynamic_database.db'):
        # Create your connection.
        try:
            conn_db = sqlite3.connect(dbname)
            self.dynamic_data = pd.read_sql_query("SELECT * FROM product_data", conn_db)
            print("dynamic_data LOADED")
        except Exception as e:
            self.dynamic_data = None
            print("dynamic_data NOT LOADED")
            print(e)
            pass

    # get all data into dataframe  
    def _read_csv(self, FILE_NAME):
        try:
            
            self.df = pd.read_csv(FILE_NAME)
            #print(self.df.head()) 
        except Exception as e:
            print(e)

    # spell correction method to correct misspelled words of user
    def spell_correction(self, keyword):
        corrected_keyword = TextBlob(keyword)
        return corrected_keyword.correct()

    # data pre processing task on features
    def data_pre_processing(self):
        '''
        select parameter and do preprocessing on data
        '''
        try:
            # remove null records 
            self.df['features'].dropna(inplace=True)
            
            # convert to lower case
            self.df["features"] = self.df["features"].str.lower() 
            #print(self.df['features'])
        
        except Exception as e:
            print(e)

    def feature_selection(self):
        try:
            # Uncomment this one based on requirement (Check speed in r_d folder)
            # self.selected_features = ['Product Title', 'Product Detail', 'Ingredients']
            # self.df['features'] = self.df[self.selected_features].agg(' '.join, axis=1)#.str.replace('\s+', ' ')
            # self.df['features'] = self.df[self.selected_features].astype(str).apply(lambda x: ' '.join(x), axis=1)
            # self.df['features'] = self.df[self.selected_features].astype(str).sum(axis=1)
            t5 = time.time()
            self.df['features'] = self.df['Product Title'].astype(str) + ' ' + self.df['Product Detail'].astype(str) + ' ' + self.df['Ingredients'].astype(str) + ' ' + self.df['Product Price'].astype(str) + ' ' + self.df['Product Volume'].astype(str)  + ' ' + self.df['Nutritional_information'].astype(str) + ' ' + self.df['Allergen warnings'].astype(str) + ' ' + self.df['Claims'].astype(str) + ' ' + self.df['Endorsements'].astype(str) + ' ' + self.df['Product origin'].astype(str)
            t6 = time.time()
            print("Time 3: ", t6-t5)
            # print(self.df['features'])
        except Exception as e:
            print(e)

    # this function is use to check tokanization works properly 
    def tokanization(self):
        #print(self.df['Product Title'])
        try:    
            nltk.sent_tokenize("Hello world")
        except Exception as e:
            # consume some time while first run
            nltk.download('punkt') # use only for first-time
            nltk.download('wordnet') # use only for first-time

    # WordNet is a semantically-oriented dictionary of English included in NLTK.
    def LemmeTokens(self, tokens):
        self.lemmer_obj = nltk.stem.WordNetLemmatizer()
        return [self.lemmer_obj.lemmatize(token) for token in tokens]

    # this method is user for remove lemmas form words: e.g : milks -> milk, eggs -> egg
    def LemNormalize(self, text):
        self.remove_punctuation_dict = dict((ord(punct), None) for punct in string.punctuation)
        return self.LemmeTokens(nltk.word_tokenize(text.lower().translate(self.remove_punctuation_dict)))

    # this function is use to initilize vectorization method
    def init_vectorization(self, my_preference):
        try:
            #self.TfidfVec = TfidfVectorizer(ngram_range=(1, 2),stop_words = "english", lowercase = True, max_features = 500000) 

            # Any preference contain 2 or more word than we initialized n-gram else without n-gram
            if len(my_preference) != 0:
                if any(len(x.split()) > 1 for x in my_preference):
                    print("Found a match, init with n-gram")
                    self.HashVec = HashingVectorizer(ngram_range=(1, 2), stop_words="english", lowercase=True)
                else:
                    print("Not a match, init without n-gram")
                    self.HashVec = HashingVectorizer(stop_words="english", lowercase=True)
            else:
                self.HashVec = HashingVectorizer(stop_words="english", lowercase=True)

        except Exception as e:
            # in case of any Exception
            self.HashVec = HashingVectorizer(stop_words="english", lowercase=True)

            print(e)

    # # general function to find distances using TFIDF
    # def find_tfidf_and_cosine_old(self, input_data, search_data):
    #     # Create list and append user input
    #     input_data.append(str(search_data))
    #     # generate new sparse matrix of tfidf
    #     tfidf = self.TfidfVec.fit_transform(input_data)
    #     # find recommendations on user keyword using cosine similarity
    #     distances = cosine_similarity(tfidf[-1], tfidf)
    #     return distances[0][:-1]

    # NEW function to find distances using TFIDF
    def find_tfidf_and_cosine(self, input_data, search_data):
        # Create list and append user input   
        input_data.append(str(search_data))
        t7 = time.time()
        # generate new sparse matrix of tfidf
        tfidf = self.HashVec.fit_transform(input_data)
        t8 = time.time()
        print("Time for vector generation: ", t8-t7)
        # find recommendations on user keyword using cosine similarity
        t9 = time.time()
        distances = cosine_similarity(tfidf[-1], tfidf)
        t10 = time.time()
        print("Time to find distance: ", t10-t9)

        return distances[0][:-1]

    # Data order manipulation (implementation of priority 1 & 2 rest of product are listed after p2 (i.e, priority 3))
    def get_relevance_sorted_product_with_user_priority(self, recommendation_list, USER_PREFERENCE_TEXT):
        
        # detect none user PREFERENCE
        if USER_PREFERENCE_TEXT == '':
            return recommendation_list

        # else modify list using priority
        else:
            USER_PREFERENCE_TEXT = USER_PREFERENCE_TEXT.lower()

            recommendation_list['features_priority_1'] = recommendation_list['Product Title'].astype(str) + ' ' + recommendation_list['Category'].astype(str)

            # Priority 1 : user input title + words from USER_PREFERENCE
            title_data = recommendation_list['features_priority_1'].values.tolist()
            
            # find distance with title
            recommendation_list['distances_1'] = self.find_tfidf_and_cosine(title_data, USER_PREFERENCE_TEXT)

            # # filter distance using THRESHOLD
            # THRESHOLD > 2.1 for get products form only title. (distances_1>=2.1 sava as it is)
            # CASE 1 Output
            recommendation_list_priority1 = recommendation_list[recommendation_list['distances_1'] >= 1.3/100].sort_values(by=['distances_1'], ascending=False)

            # CASE 2 / Priority 2 user input + PREFERENCE + other attributes 
            # select column form recommendation_list for priority 2 and further process 
            recommendation_list_priority2 = recommendation_list[recommendation_list['distances_1'] < 1.3/100].sort_values(by=['distances_1'], ascending=False)

            #Select other features for case 2
            recommendation_list_priority2['features_priority_2'] = recommendation_list_priority2['Product Title'].astype(str) + ' ' + recommendation_list_priority2['Category'].astype(str) + ' ' +recommendation_list_priority2['Ingredients'].astype(str) + ' ' + recommendation_list_priority2['Nutritional_information'].astype(str) + ' ' + recommendation_list_priority2['Allergen warnings'].astype(str) + ' ' + recommendation_list_priority2['Claims'].astype(str) + ' ' + recommendation_list_priority2['Endorsements'].astype(str)
            
            other_data = recommendation_list_priority2['features_priority_2'].values.tolist()

            # find distance with other data
            recommendation_list_priority2['distances_2'] = self.find_tfidf_and_cosine(other_data, USER_PREFERENCE_TEXT)

            # sort data CASE 2
            recommendation_list_priority2 = recommendation_list_priority2.sort_values(by=['distances_2'], ascending=False)
            
            #print("New LEN: ", len(recommendation_list_priority2.index))
            #print(recommendation_list_priority2)

            # merge all data
            recommendation_list_priority1 = recommendation_list_priority1.append(recommendation_list_priority2, ignore_index = True)
            #print(recommendation_list_priority1)

            # Delete processed column
            del recommendation_list_priority1['features_priority_1']
            del recommendation_list_priority1['distances_1']
            del recommendation_list_priority1['features_priority_2']	
            del recommendation_list_priority1['distances_2']	
            	

        return recommendation_list_priority1

    # map category with USER_PREFERENCE
    def map_user_preference(self, USER_PREFERENCE=[]):
        # case: USER_PREFERENCE is none then use main categories only
        if len(USER_PREFERENCE) == 0:
            return ''
        else:
            my_preference = ''
            for preference in USER_PREFERENCE:
                # print(preference)
                if preference.lower() == "organic":
                    my_preference += 'organic Fruit & Veg Meat & Seafood Baby & Child Fridge & Deli Bakery Pantry Drinks Beer & Wine Ice Cream & Sorbet Health & Beauty '
                elif preference.lower() == "non gmo":
                    my_preference += 'non gmo Fruit & Veg Frozen Baby & Child Fridge & Deli Bakery Pantry '
                elif preference.lower() == "pesticide free":
                    my_preference += 'pesticide free Fruit & Veg Meat & Seafood Baby & Child Fridge & Deli Pantry '
                elif preference.lower() == "free range":
                    my_preference += 'Free Range Eggs Meat & Seafood Frozen Meat Fridge & Deli Pantry Pet Cage free'
                elif preference.lower() == "nut free":
                    my_preference += 'nut free Frozen Fridge & Deli Bakery Pantry '
                elif preference.lower() == "dairy free":
                    my_preference += 'dairy free Frozen Meat & Seafood Baby & Child Fridge & Deli Bakery Pantry Pet Ice Cream & Sorbet '
                elif preference.lower() == "palm oil free":
                    my_preference += 'palm oil free Frozen Meat & Seafood Baby & Child Fridge & Deli Bakery Pantry Pet '
                elif preference.lower() == "additives free":
                    my_preference += 'additives free Frozen Meat & Seafood Baby & Child Fridge & Deli Bakery Pantry Pet Ice Cream & Sorbet Health & Beauty'
                elif preference.lower() == "sugar free":
                    my_preference += 'sugar free Frozen Meat & Seafood Baby & Child Fridge & Deli Bakery Pantry Pet '
                elif preference.lower() == "gluten free":
                    my_preference += 'gluten free Frozen Meat & Seafood Baby & Child Fridge & Deli Bakery Pantry Pet Ice Cream & Sorbet '
                elif preference.lower() == "vegan":
                    my_preference += 'vegan Frozen Meat & Seafood Baby & Child Fridge & Deli Bakery Pantry Pet Ice Cream & Sorbet '
                elif preference.lower() == "halal":
                    my_preference += 'halal Frozen Meat & Seafood Baby & Child Fridge & Deli Bakery Pantry Pet Ice Cream & Sorbet Health & Beauty '
            my_preference = my_preference.lower()
        return my_preference

     # Check collocation of the preference to improve the accuracy in case of 'Non GMO', 'Sugar Free' etc
    def collocation(self, KEYWORD, USER_PREFERENCE=[]):
        # print(KEYWORD.lower().split(" "))
        other_words = ['no', 'non', 'free', 'zero']
        # loop for all word in user input
        for word in KEYWORD.lower().split(" "):
            # loop to check other_words present or not
            if word in other_words:
                # Auto change user preference based on user text input
                # Check word is present in input KEYWORD
                if (KEYWORD.lower().find('organic') != -1):
                    # if found change preference
                    try:
                        # Remove word
                        KEYWORD = KEYWORD.replace("organic", "").strip()
                        # Remove from preference
                        USER_PREFERENCE.remove('Organic')
                    except Exception as e:
                        print(e)
                        pass
                elif (KEYWORD.lower().find('gmo') != -1):
                    try:
                        # Remove word
                        KEYWORD = KEYWORD.replace("gmo", "").strip()
                        # Append into preference
                        USER_PREFERENCE.append('Non GMO')
                    except Exception as e:
                        print(e)
                        pass
                elif (KEYWORD.lower().find('pesticide') != -1):
                    try:
                        # Remove word
                        KEYWORD = KEYWORD.replace("pesticide", "").strip()
                        # Append into preference
                        USER_PREFERENCE.append('Pesticide Free')

                    except Exception as e:
                        print(e)
                        pass
                elif (KEYWORD.lower().find('range') != -1):
                    try:
                        # Remove word
                        KEYWORD = KEYWORD.replace("range", "").strip()
                        # Append into preference
                        USER_PREFERENCE.append(['Free Range', 'Cage free'])
                    except Exception as e:
                        print(e)
                        pass
                elif (KEYWORD.lower().find('nut') != -1):
                    try:
                        # Remove word
                        KEYWORD = KEYWORD.replace("nut", "").strip()
                        # Append into preference
                        USER_PREFERENCE.append('Nut Free')
                    except Exception as e:
                        print(e)
                        pass
                elif (KEYWORD.lower().find('dairy') != -1):
                    try:
                        # Remove word
                        KEYWORD = KEYWORD.replace("dairy", "").strip()
                        # Append into preference
                        USER_PREFERENCE.append('Dairy Free')
                    except Exception as e:
                        print(e)
                        pass
                elif (KEYWORD.lower().find('oil') != -1):
                    try:
                        # Remove word
                        KEYWORD = KEYWORD.replace("oil", "").strip()
                        # Append into preference
                        USER_PREFERENCE.append('Palm oil Free')
                    except Exception as e:
                        print(e)
                        pass
                elif (KEYWORD.lower().find('additives') != -1):
                    try:
                        # Remove word
                        KEYWORD = KEYWORD.replace("additives", "").strip()
                        # Append into preference
                        USER_PREFERENCE.append(['Flavour', 'Stabiliser', 'Emulsifier', 'Antioxidant', 'Preservative'])
                    except Exception as e:
                        print(e)
                        pass
                KEYWORD = KEYWORD.replace(word, "").strip()
            else:
                pass
        return KEYWORD, USER_PREFERENCE

    # this function will help to get recommendations
    def recommendations_from_keyword(self, KEYWORD, THRESHOLD = 2, USER_PREFERENCE=[]):
        try: 
            # null input condition get recommendation based on preference
            if KEYWORD == '': 
                self.recommendation_list = None
                self.legnth_recommendation_list = 0
                self.empty_flag = True
                return self.recommendation_list, self.legnth_recommendation_list, self.empty_flag

            # Function collocation manipulate user preference
            KEYWORD, USER_PREFERENCE = self.collocation(KEYWORD, USER_PREFERENCE)
            print("collocation: ", KEYWORD, USER_PREFERENCE)
            # Generate plural form of key word and append into KEYWORD itself
            plural = self.inflect_engine.plural(KEYWORD)
            KEYWORD += " " + plural
            print("Add plural:", KEYWORD)

            # map category with USER_PREFERENCE
            USER_PREFERENCE_TEXT = self.map_user_preference(USER_PREFERENCE)
            # print(USER_PREFERENCE_TEXT)

            KEYWORD = KEYWORD.lower()
            #print(KEYWORD)
            
            # RL based TOP priority

            self.dynamic_data_title = self.dynamic_data['Product Title'].values.tolist()

            self.dynamic_data['distances'] = self.find_tfidf_and_cosine(self.dynamic_data_title, KEYWORD)

            # filter distance using THRESHOLD and sort by RL weight
            self.dynamic_list_1 = self.dynamic_data[self.dynamic_data['RL_weight'] >= 0].sort_values(by=['RL_weight'], ascending=False)

            self.length_dynamic_list_1 = len(self.dynamic_list_1.index)

            # get top weight products dataframe
            print(self.length_dynamic_list_1)
            print(self.dynamic_list_1)

            # Standard listing without RL
            # Create list and append user input   
            self.data_list = self.df['Product Title'].values.tolist()
            
            # Priority 4 : (GET all product associated with keyword using title)
            self.df['distances'] = self.find_tfidf_and_cosine(self.data_list, KEYWORD)

            # filter distance using THRESHOLD
            self.recommendation_list = self.df[self.df['distances'] >= THRESHOLD/100].sort_values(by=['distances'], ascending=False)
            
            self.legnth_recommendation_list = len(self.recommendation_list.index)
            
            # for empty recommendation_list :: Helps to dispaly 'no product available with this key word' in site  
            if self.legnth_recommendation_list == 0:
                self.empty_flag = True
            else: 
                self.empty_flag = False
            
            try:
                # Data order manipulation with three priority
                self.recommendation_list = self.get_relevance_sorted_product_with_user_priority(self.recommendation_list, KEYWORD +" "+ USER_PREFERENCE_TEXT)
            except Exception as e:
                print('Error in Data order manipulation',e)
                pass
            
            # remove features and distances column from output data
            del self.recommendation_list['features']
            del self.recommendation_list['distances']

            # merge RL data and standard data without RL
            self.recommendation_list = self.dynamic_list_1.append(self.recommendation_list, ignore_index = True)

            #print(self.recommendation_list)
            #################################################################################
            # Uncomment this part if you required to recommended product only in fix number 
            # n = 5
            # n_largest = self.df['distances'].nlargest(n + 1)
            # print(n_largest)
            # print(self.df['Product Title'].iloc[self.df['distances'].nlargest(n + 1)])
            #################################################################################
        
        except Exception as e:
            # incase of error in script no recommendation
            self.recommendation_list = None
            self.legnth_recommendation_list = 0
            self.empty_flag = True
            print(e)

        return self.recommendation_list, self.legnth_recommendation_list, self.empty_flag


# Main method contains input method. This can be change according to requirement from below
if __name__ == "__main__":
    try:
        # Create folder data
        import os 
        if not os.path.exists('Recommendation_results'):
            os.makedirs('Recommendation_results')
        
        while True :
            print("\nEnter your keyword: ")
            keyword = str(input())

            # create Object of Recommendation_Engine     
            t1 = time.time()
            recommendation_engine = Recommendation_Engine()
            t2 = time.time()
            print("Time 1: ", t2-t1)
            # GET recommendation list form recommendations_from_keyword method 
            
            # Value of THRESHOLD is optional and vary between [0 to 100] 

            # which is a matching threshold use for remove totaly irrelevant products(e.g high THRESHOLD -> low output)

            # user_preference key word / text line add here which works as defualt search for empty input 

            # empty_flag is for empty recommendation_list :: Helps to dispaly 'no product available with this key word' in site
            t3 = time.time()
            
            recommendations, len_of_list, empty_flag = recommendation_engine.recommendations_from_keyword(keyword, THRESHOLD= 2, USER_PREFERENCE_TEXT= 'Nuts Chocolate')
            t4 = time.time()
            print("Time 2: ", t4-t3)

            # check full data frame
            #print(recommendations)

            recommendations.to_csv( 'Recommendation_results/'+ keyword+'_results.csv') 
            # see only title
            print(recommendations['Product Title'])
            print('Length of recommendation list : ', len_of_list)
            print('Flag represent recommendation list is empty(True) or not(False): ', empty_flag)
    
    except Exception as e:
        print(e)