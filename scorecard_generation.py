############################################################################

# This file contain receipt scanning and score generation from user purchase. 
# Class Scorecard_generation can easily separable for future use. 
# Main method is available below to play with receipt images

############################################################################
import pytesseract
import cv2
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.ndimage import interpolation as inter
import numpy as np
from spellchecker import SpellChecker

# change path if required / for mac os just comment this line
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/Cellar/tesseract/4.1.1/bin/tesseract'

# for windows
# pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

import streamlit as st
import pandas as pd

class Scorecard_generator:
    def __init__(self):
        # initialize of vectorization
        self.init_vectorization()

        # correct spelling up to 2 distance
        self.spell = SpellChecker(distance=2)  # set at initialization

    # This function is use to initialize vectorization method
    def init_vectorization(self):
        try:
            self.vectorizer = CountVectorizer(stop_words = "english", lowercase = True) 

        except Exception as e:
            print(e)

    def correct_spell(self, mess):
        arr = mess.split()
        mess1 = []
        for word in arr:
            mess1.append(self.spell.correction(word))
        mess1 = " ".join(mess1)
        return mess1

    # general function to find distances using CountVectorizer
    def find_distances_and_cosine(self, receipt_data, user_preference):
        # Create list and append user input   
        data_arr = [user_preference, receipt_data]
        #print(data_arr)

        # generate new sparse matrix using CountVectorizer
        count_matrix = self.vectorizer.fit_transform(data_arr)
        
        # find distances on receipt_data using cosine similarity
        cosine_sim = cosine_similarity(count_matrix)

        #  This is a cosine matrix our score present at element no (0,1) or (1,0)
        # [[1.         0.27773186]
        #  [0.27773186 1.        ]]
        #print(cosine_sim)

        score = cosine_sim[0][1] 

        return score

    # This function perform Image preprocessing step on input image to extract meaning full data
    def receipt_pre_processing(self, image):
        # Binarization
        # convert the image to binary image... for better OCR
        ret,thresh1 = cv2.threshold(image,165,255,cv2.THRESH_BINARY, cv2.THRESH_OTSU)

        # Skew Correction
        _, rotated = self.correct_skew(thresh1)
        #print(angle)
        
        return rotated


    # This function is used to correct skew of the image... Image available in R&d for better understanding
    def correct_skew(self,image, delta=1, limit=5):
        def determine_score(arr, angle):
            data = inter.rotate(arr, angle, reshape=False, order=0)
            histogram = np.sum(data, axis=1)
            score = np.sum((histogram[1:] - histogram[:-1]) ** 2)
            return histogram, score

        scores = []
        angles = np.arange(-limit, limit + delta, delta)
        for angle in angles:
            histogram, score = determine_score(image, angle)
            scores.append(score)

        best_angle = angles[scores.index(max(scores))]

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, \
                borderMode=cv2.BORDER_REPLICATE)

        return best_angle, rotated

    # Function to replace multiple character from line
    def replaceMultiple(self,mainString, toBeReplaces, newString):
        # Iterate over the strings to be replaced
        for elem in toBeReplaces :
            # Check if string is in the main string
            if elem in mainString :
                # Replace the string
                mainString = mainString.replace(elem, newString)
        
        return  mainString 

    # Text pre processing
    def OCR_text_pre_preprocessing(self, text):
        # convert to lower
        text = text.lower()

        # remove other words then text
        text = re.sub('[^a-zA-Z]', ' ', text)

        # uncomment to use spell corrector
        text = self.correct_spell(text)
        # print(text)

        # remove common words of receipt
        text = self.replaceMultiple(text, ["countdown"," shop","smarter"], "")

        #convert multiple white space to single
        text = re.sub(' +', ' ', text)
        
        return text

    # This function is used to increase your distance value with certain parameters 
    # Because we will never get 100% match with only distance. This function will help to get 100 % matching
    def get_normalized_score(self, distance, threshold=0.37):
        # increase score value
        linear_val = (distance / (threshold * 2.0))
        # set > 1 value to 1
        if linear_val > 1.0: linear_val = 1.0

        # Get percentage 
        linear_val *= 100

        return int(linear_val)

    # get_text_from_receipt using OCR
    def get_text_from_receipt(self, image):
        # OCR on image to string to get results
        extracted_data = str(pytesseract.image_to_string(image, config='--psm 6'))
        return extracted_data

    # 2nd method to score calculation
    # implemented here because of it's required to load data every time but using cache it can be load one time only
    # This is one time running function
    @st.cache(suppress_st_warning=True, allow_output_mutation=True)  
    def expensive_computation_load_data(self):
        # reading csv file from url 
        # data = pd.read_csv("all_product_data.csv")
        # print("Data Loaded")
        try:
            conn_db = sqlite3.connect('dynamic_database.db')
            data = pd.read_sql_query("SELECT * FROM product_data", conn_db)
            # print(data)
            print("dynamic_data LOADED")
        except Exception as e:
            data = None
            print("dynamic_data NOT LOADED")
            print(e)
            pass



        return data

    def get_product_description_from_csv(self, data, product_name):
        try:
            
            # substring to be searched

            # creating and passing series to new column
            data_index = data["ProductTitle"].str.find(product_name)

            print("product_name", product_name)
            #blob_pname = TextBlob(product_name)
            #product_name = str(blob_pname.correct())
            #print("correct product_name", product_name)

            # Check product is present in our data base if not pass
            if data_index.max() != -1:

                data_all = data.iloc[data_index.argmax()]

                text_description = data_all[['ProductTitle', 'ProductDetail', 'Ingredients', 'Nutritional_information', 'Allergenwarnings', 'Claims', 'Endorsements']].to_string(header=False, index=False)

                # remove other words then text
                text_description = re.sub('[^a-zA-Z]', ' ', text_description)

                # remove common words of receipt
                text_description = self.replaceMultiple(text_description, ["NaN"," shop","smarter"], "")

                #convert multiple white space to single
                text_description = re.sub(' +', ' ', text_description)

                #print(text_description)
                #print(type(text_description))

                #------- R & D stuff ----------#
                
                #blob = TextBlob(text_description)
                #text_description = str(blob.correct())
                # prints the corrected spelling
                #print("corrected text: "+str(blob.correct()))
                #text_description = data.values.tolist()
                #text_description = ' '.join(str(v) for v in text_description)
                #discription_out['features'] = discription_out['Product Title'].astype(str) + ' ' + discription_out['Product Detail'].astype(str) + ' ' + discription_out['Ingredients'].astype(str) + ' ' + ' ' + discription_out['Nutritional_information'].astype(str) + ' ' + discription_out['Allergen warnings'].astype(str) + ' ' + discription_out['Claims'].astype(str) + ' ' + discription_out['Endorsements'].astype(str) 

                #text_description = discription_out["Name"].str.cat(new, sep =", ")
                #print(data['features'])
                #text_description = data.apply(' '.join, axis=1)

                #text_description = discription_out["Product Title", "Product Detail"].astype(str).apply(''.join, axis=1)
                #print(product_name)
                #print("WE ARE HERE")
                #print("-----------------------------")
                #text_description = discription_out['Product Title'] + ' ' + discription_out['Product Detail'] + ' ' + str(discription_out['Ingredients']) + ' ' + str(discription_out['Nutritional_information']) + ' ' + str(discription_out['Allergen warnings']) + ' ' + str(discription_out['Claims'])#.astype(str)

                # add space to merge next product
                text_description += " "

            else: # no product match with our data
                text_description = ''

        except Exception as e:
            print(e)
            text_description = ""
            


        return text_description


    # this function generate score from product discription
    def generate_product_list_and_get_score(self,extracted_data, USER_PREFERENCE_TEXT):
        description_score = 0
        try:
            #description_text from all products
            description_text = ''
            if extracted_data.strip() !="":
                # load data
                data = self.expensive_computation_load_data()
                product_list = extracted_data.split("\n")
                print(product_list)
                for idx, product in enumerate(product_list):
                    try:
                        # remove all text without price [Filter 1]
                        if re.findall(r"\d+",product):
                            # remove most common lines [Filter 2]
                            if product.find("PH:") == -1 and product.find("GST") == -1 and product.find("@") == -1 and product.find("MERCH") == -1 and product.find("www") == -1: 

                                # Uncomment to use spell corrector for product search to raw data
                                product = self.correct_spell(product)

                                # find exact product name from product list with prices and quantity [Filter 3]
                                product = re.split(r'(\s\d)', product)
                                
                                # search product in our csv file
                                
                                description_text += self.get_product_description_from_csv(data, product[0])


                    except Exception as e:
                        print(e)
                        pass

            # description_text
            # Standard function to find distances using CountVectorizer
            print("description_text",description_text)
            description_score = self.find_distances_and_cosine(description_text, USER_PREFERENCE_TEXT)
            description_score = self.get_normalized_score(description_score)
            print("description_score", description_score)
        except Exception as e:
            print(e)
            pass

        return int(description_score)


    # one function call to access everything
    def get_score_from_receipt(self, image, USER_PREFERENCE_TEXT= ['Organic']):

        # Merge preferences
        if len(USER_PREFERENCE_TEXT) != 0:
            USER_PREFERENCE_TEXT = ' '.join(USER_PREFERENCE_TEXT)
        else:
            USER_PREFERENCE_TEXT = ' '
        USER_PREFERENCE_TEXT = USER_PREFERENCE_TEXT.lower()

        normalized_score = 0
        # image preprocessing
        image = self.receipt_pre_processing(image)

        # Text extraction
        extracted_data = self.get_text_from_receipt(image)
        #print(extracted_data)

        #####################################################################
        # 2nd method to increase score
        normalized_score += self.generate_product_list_and_get_score(extracted_data, USER_PREFERENCE_TEXT)
        print("--------")


        #####################################################################
        # old Score 1st method
        # Process OCR text
        extracted_data = self.OCR_text_pre_preprocessing(extracted_data)
        #print(extracted_data)
        # exceptional case if text not found in image
        if extracted_data.strip() !="":
            print(extracted_data)
            # blob_1 = TextBlob(extracted_data)
            # extracted_data = str(blob_1.correct())
            # # prints the corrected spelling
            # print("corrected text: "+str(blob_1.correct()))
            # # Standard function to find distances using CountVectorizer
            score = self.find_distances_and_cosine(extracted_data, USER_PREFERENCE_TEXT)
            #print(score)
            # This function is used to increase your distance value with certain parameters 
            # Becasue we never get 100 Percent match with only distance. This function will help to get 100 % matching
            normalized_score += self.get_normalized_score(score)
            #print("score from 1st method", score)
        else :
            normalized_score += 0
        #####################################################################
        return normalized_score, image

# Main method contains input method. This can be change according to requirement from below
if __name__ == "__main__":
    try:
        import sys
        # create Object of Scorecard_generation     
        scorecard_obj = Scorecard_generator()
        while True :
            #print("\nEnter image path: ")
            image_path = sys.argv[1] #'2.jpg'#str(input())
            # load the original image
            image = cv2.imread(image_path)

            # one function call to access everything
            output_score, image = scorecard_obj.get_score_from_receipt(image, USER_PREFERENCE_TEXT= 'Organic milk std hb crm frsksoohl')
            print(output_score)
            cv2.imshow('image',image)
            cv2.waitKey(0)
            break
    except Exception as e:
        print(e)