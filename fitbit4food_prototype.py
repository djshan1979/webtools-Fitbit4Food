##############################################################################################

# This file contain Streamlit dashboard for recommendation engine
# pip install streamlit
# RUN : streamlit run streamlit_recommedation_engine.py
##############################################################################################

import streamlit as st 
import streamlit.components.v1 as stc
from recommendation_engine import Recommendation_Engine
import SessionState
import os
from datetime import datetime
import numpy as np
import cv2
from scorecard_generation import Scorecard_generator

HTML_TITLE = """
	<div style="background-color:#D4EFDF;padding:10px;border-radius:10px">
	<h1 style="color:#1E8449;text-align:center;">Fitbit4Food</h1>
	</div>
	"""

# create object of score card generator backend
scorecard_obj = Scorecard_generator()

session_state = SessionState.get(page_number = 0)

@st.cache
def save_image(file):
	#if file is too large then return
	if file.size > 209715200: # 200 MB
		return 1
	
	folder = "public_receipt_images"
	datetoday = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	
	# clear the folder to avoid storage overload (will use when required)
	# for filename in os.listdir(folder):
	# 	file_path = os.path.join(folder, filename)
	# 	try:
	# 		if os.path.isfile(file_path) or os.path.islink(file_path):
	# 			os.unlink(file_path)
	# 	except Exception as e:
	# 		print('Failed to delete %s. Reason: %s' % (file_path, e))

	try:
		with open("log0.txt", "a") as f:
			f.write(f"{file.name} - {file.size} - {datetoday};\n")
	except:
		pass

	with open(os.path.join(folder, file.name), "wb") as f:
		f.write(file.getbuffer())
	return 0

# GUI function for dashboard
def recommendation_engine_gui():
	
	# initialize menu and add to visual HTML(Front End)
	menu = ["Home","Scan receipt"]
	choice = st.sidebar.selectbox("Options",menu)

	# initialize preference_option and add to visual HTML(Front End)
	preference_option = ["All", "Organic", "Non GMO", "Pesticide Free", "Free Range", "Nut Free", "Dairy Free", "Palm Oil Free", "Additives Free", "Sugar Free", "Gluten Free", "Vegan", "Halal", "None"]
	my_preference_preset = 'None'

	# preset user profile
	preset = ["None", "Healthy Helena", "Sustainable Sally", "Dietary Dave", "Price Conscious Peter", "Only Organic Olivia"]
	user_preset = st.sidebar.selectbox("Preset User Profile",preset)

	# Title 'NLP based recommendation engine' into HTML
	stc.html(HTML_TITLE)

	# Select All Preferences option
	if user_preset == "Healthy Helena":
		my_preference_preset = ["Additives Free", "Sugar Free", "Dairy Free", "Gluten Free", "Vegan"]
	elif user_preset == "Sustainable Sally":
		my_preference_preset = ["Organic", "Free Range", "Vegan", "Non GMO", "Palm Oil Free", "Pesticide Free"]
	elif user_preset == "Dietary Dave":
		my_preference_preset = ["Halal", "Vegan", "Gluten Free", "Dairy Free", "Sugar Free"]
	elif user_preset == "Only Organic Olivia":
		my_preference_preset = ["Organic"]
	else:
		pass

	# Set user preference
	my_preference = st.sidebar.multiselect("Set your preferences (priority wise)", preference_option, default=my_preference_preset)

	if "All" in my_preference:
		my_preference = ["Organic", "Non GMO", "Pesticide Free", "Free Range", "Nut Free", "Dairy Free", "Palm Oil Free", "Additives Free", "Sugar Free", "Gluten Free", "Vegan", "Halal"]

	print("my_preference_preset: ", my_preference_preset)

	# create object of our backend script
	recommendation_engine = Recommendation_Engine(my_preference)

	# Home option
	if choice == "Home":

		# initialize sorting option and add to visual HTML(Front End)
		sort_option = ["Relevance", "Price Low to High","Price High to Low", "Unit Price Low to High"]
		sort_by = st.sidebar.selectbox("Sort By", sort_option)
		
		# set sub header
		st.subheader("Search Product")

		# Take user input
		product_name = st.text_input("Enter Product name")
		
		# initialize and add search button into HTML
		submit = st.button('Search')

		# Enable mouse click or keyboard "enter / return " key to search product
		if submit or product_name:
			
			if product_name.strip() == '':
				final_keyword = 'food'	# if keyword is blank, default value is set to food
			else:
				final_keyword = product_name.lower()
				final_keyword = scorecard_obj.correct_spell(final_keyword)

			# Get recommendation using our object (Only single function call)
			# TODO: ADD GUI for empty_flag if product list is empty
			print("my_preference: ",my_preference)
			recommendations, len_of_list, empty_flag = recommendation_engine.recommendations_from_keyword(final_keyword, THRESHOLD= 2, USER_PREFERENCE= my_preference)

			# Condition if user input is empty -> pass user preference  
			if final_keyword.strip() == '':
				TOTAL_PRODUCTS = """
					<div style="background-color:#464e5e;padding:10px;border-radius:10px">
					<h3 style="color:white;text-align:center;">Please enter product name  "{product_name}":  About <b>{len_of_list}</b> products recommended </h3>
					</div>
					""".format(len_of_list = len_of_list, product_name = '')

			else:			# Condition else user input is merged with user preference
				TOTAL_PRODUCTS = """
					<div style="background-color:#464e5e;padding:10px;border-radius:10px">
					<h3 style="color:white;text-align:center;">Results for "{product_name}":  About <b>{len_of_list}</b> products recommended </h3>
				</div>
					""".format(len_of_list = len_of_list, product_name = final_keyword)
			
			# Display 'Results for...' tag into html 
			stc.html(TOTAL_PRODUCTS, height = 100)

			# Manage sorting option
			if sort_by == 'Price Low to High':
				recommendations = recommendations.sort_values(by=['Product Price'], ascending=True)
			elif sort_by == 'Price High to Low':
				recommendations = recommendations.sort_values(by=['Product Price'], ascending=False)
			elif user_preset == 'Price Conscious Peter' or sort_by == 'Unit Price Low to High':
				recommendations = recommendations.sort_values(by=['price per base volume'], ascending=True)
			else:
				pass

			# uncomment this to see dataframe without html
			#st.dataframe(data=recommendations)
			
			try: 
				# HTML + logic to display list of product
				# Number of entries per screen
				N = 15

				# A variable to keep track of which product we are currently displaying
				#page_number = 0

				last_page = len(recommendations) // N

				# Add a next button and a previous button
				prev, _ , page_reset , _ , next = st.beta_columns([1,2,2,2,1])

				if next.button("Next"):

					if session_state.page_number + 1 > last_page:
						session_state.page_number = 0
					else:
						session_state.page_number += 1

				if prev.button("Previous"):

					if session_state.page_number - 1 < 0:
						session_state.page_number = last_page
					else:
						session_state.page_number -= 1

				if page_reset.button("Reset Page"):
					session_state.page_number = 0
				else:
					pass

				# Get start and end indices of the next page of the dataframe
				start_idx = session_state.page_number * N 
				end_idx = (1 + session_state.page_number) * N

				CURRENT_PAGE = """
					<div style="background-color:#464e5e;padding:1px;border-radius:1px">
						<h4 style="color:white;text-align:center;vertical-align:middle;"> Current Page: "{current_page}" </h4>
					</div>
						""".format(current_page=session_state.page_number)

				# Display current page
				page = stc.html(CURRENT_PAGE, height = 60)

				# Index into the sub dataframe
				sub_recommendations = recommendations.iloc[start_idx:end_idx]

				# uncomment this line to see sub list
				#st.write(sub_recommendations)

				# Select required column
				myrows = zip(sub_recommendations['URL'], sub_recommendations['Product Title'], sub_recommendations['Product Image'], sub_recommendations['Product Price'], sub_recommendations['Product Volume'], sub_recommendations['Category'], sub_recommendations['Product Detail'], sub_recommendations['Ingredients'], sub_recommendations['Nutritional_information'], sub_recommendations['Allergen warnings'], sub_recommendations['Claims'], sub_recommendations['Endorsements'], sub_recommendations['Product origin'])
				
				# html header
				PRODUCT_CARD = '''
						<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.min.css">
						<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css">
						<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
						<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
						<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
						
						<style>
							.ratings i {
								font-size: 16px;
								color: red
							}
							.btn-outline-primary:hover {
								color: #ffffff;
								background-color: rgb(131, 160, 52);
							}
							.btn-outline-primary:not(:disabled):not(.disabled):active, .show > .btn-outline-primary.dropdown-toggle {
								color: rgb(255, 255, 255);
								background-color: #2e6f22;
								border-color: rgb(0, 123, 255);
							}
							.strike-text {
								color: red;
								text-decoration: line-through
							}
							.product-image {
								width: 50%
							}
							.dot {
								height: 7px;
								width: 7px;
								margin-left: 6px;
								margin-right: 6px;
								margin-top: 3px;
								background-color: green;
								border-radius: 50%;
								display: inline-block
							}
							.spec-1 {
								color: #938787;
								font-size: 15px
							}
							h5 {
								font-weight: 400
							}
							.para {
								font-size: 16px
							}
							.modal {
								position: relative;
							}
							.dislike{
								width: 30px;
								height: 30px;
								margin: 0 auto;
								line-heigth: 50px;
								border-radius: 50%;
								color: rgb(0 150 53);
								background-color: rgb(166 38 38 / 0%);
								border-color: rgb(1 150 0)
								border-width: 1px;
								font-size: 15px;
							}

						</style>
	
						<body style = "background-color: transparent;">'''
	
				# loop on all product and generate HTML for each one and add into PRODUCT_CARD as string
				for idx, (col1,col2,col3,col4,col5,col6,col7,col8,col9,col10,col11,col12,col13) in enumerate(myrows):
							# create HTML product card

							if str(col4) == 'nan':
										availability = "Not available"
										availability_color = 'text-danger'
										col4 = "N/A"
							else:
										availability = "Available"
										availability_color = 'text-success'

							# convert category string to list
							if len(col6) > 4:
									import ast
									col6_array = ast.literal_eval(col6)
									# print(col6_array)
									# print(type(col6_array))
									category_html = '''<div class="mt-1 mb-1 spec-1">'''
									for i in col6_array:
										category_html += '''<span class="dot"></span> <span>{value}</span>'''.format(value=i)
									category_html += "<br></div>"

							if str(col7) == 'nan':
										col7 = "No Information to display"
							if str(col8) == 'nan':
										col8 = "No Information to display"
							if str(col9) == 'nan':
								col9 = "No Information to display"
							else:
								col9_for_Json = col9.replace('"','\\"')
							if str(col10) == 'nan':
										col10 = "No Information to display"
							if str(col11) == 'nan':
										col11 = "No Information to display"
							if str(col12) == 'nan':
										col12 = "No Information to display"
							if str(col13) == 'nan':
										col13 = "No Information to display"

							# print(col9_for_Json)
							
							PRODUCT_CARD += '''
							<!-- The Modal -->
							<div class="modal" id="card_{idx}">
								<div class="modal-dialog modal-dialog-scrollable">
								<div class="modal-content">
								
									<!-- Modal Header -->
									<div class="modal-header">
									<h4 class="modal-title">{title}</h4>
									<button type="button" class="close" data-dismiss="modal">&times;</button>
									</div>

									<!-- Modal body -->
									<div class="modal-body">

										<p>
										<button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#product_detail" style = "background-color: #2e6f22; border-color: #2e6f22" aria-expanded="false" aria-controls="collapse">Product Detail</button>
										</p>

										<div class="collapse" id="product_detail">
											<div class="card card-body">
												{product_detail}
											</div>
											<br>
										</div>

										<p>
											<button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#Ingredients" style = "background-color: #2e6f22; border-color: #2e6f22" aria-expanded="false" aria-controls="collapse">Ingredients</button>
										</p>

										<div class="collapse" id="Ingredients">
											<div class="card card-body">
												{Ingredients}
											</div>
											<br>
										</div>

										<p>
											<button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#nutritional_information" style = "background-color: #2e6f22; border-color: #2e6f22" aria-expanded="false" aria-controls="collapse">Nutritional Information</button>
										</p>

										<div class="collapse" id="nutritional_information">
											<div class="card card-body">
												{Nutritional_information}
											</div>
											<br>
										</div>

										<p>
											<button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#allergen_warnings" style = "background-color: #2e6f22; border-color: #2e6f22" aria-expanded="false" aria-controls="collapse">Allergen Warning</button>
										</p>

										<div class="collapse" id="allergen_warnings">
											<div class="card card-body">
												{Allergen_warnings}
											</div>
											<br>
										</div>

										<p>
											<button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#claims" style = "background-color: #2e6f22; border-color: #2e6f22" aria-expanded="false" aria-controls="collapse">Claims</button>
										</p>

										<div class="collapse" id="claims">
											<div class="card card-body">
												{Claims}
											</div>
											<br>
										</div>

										<p>
											<button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#endorsements" style = "background-color: #2e6f22; border-color: #2e6f22" aria-expanded="false" aria-controls="collapse">Endorsements</button>
										</p>

										<div class="collapse" id="endorsements">
											<div class="card card-body">
												{Endorsements}
											</div>
											<br>
										</div>

										<p>
											<button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#product_origin" style = "background-color: #2e6f22; border-color: #2e6f22" aria-expanded="false" aria-controls="collapse">Product Origin</button>
										</p>

										<div class="collapse" id="product_origin">
											<div class="card card-body">
												{product_origin}
											</div>
											<br>
										</div>
									</div>
									
									<!-- Modal footer -->
									<div class="modal-footer">
									<button type="button" class="btn btn-danger" style = "background-color: #2e6f22; border-color: #2e6f22" data-dismiss="modal">Close</button>
									</div>
								</div>
								</div>
							</div>

							<div class="container mt-2 mb-2">
								<div class="d-flex justify-content-center row">
									<div class="col-md-11">

										<div style = "background-color: #c8ffbe;" class="row p-2 border rounded">
											
											<div class="col-md-3 mt-1" style = "text-align: center;"><img class="img-fluid img-responsive rounded product-image" src="{img_link}">
											</div>
											<div class="col-md-6 mt-1">
												<h5>{title}</h5>
	
												{category_html}
												<p class="text-justify text-truncate para mb-0">{product_detail}<br><br></p>
												
											</div>
											<div class="align-items-center align-content-center col-md-3 border-left mt-1">
											
												<div class="d-flex flex-row align-items-center">
													<h4 class="mr-1">$ {price}</h4>
													<span style = "color: #d44d2f; border-color: #2e6f22;">{volume}</span>
												</div>
												<h6 class="{availability_color}">{availability}</h6>
												<button class="dislike" id="feedback_{idx}">
												<i class="fa fa-thumbs-o-down" aria-hidden="true"></i>
												</button>
												<div class="d-flex flex-column mt-4">
													<button data-toggle="modal" data-target="#card_{idx}" style = "background-color: #2e6f22; border-color: #2e6f22" class="btn btn-primary btn-sm"> <a style = "color: rgb(255, 255, 255);"> Unlock More Info </a></button>
													<button onClick="javascript:window.open('{product_link}', '_blank');" style = "color: #2e6f22; border-color: #2e6f22;" class="btn btn-outline-primary btn-sm mt-2" type="button"><a> Add to cart</a></button>
												</div>
											</div>
										</div>
									</div>
								</div>

							</div>
							<script type = "text/javascript">
							<!--
								var product_data_{idx} = {{ URL:"{product_link}", Product_Title:"{title}",tag:"",Product_Price:"{price}",Product_Volume:"{volume}",price_per_base_volume:"",Category:"{category_list}",Product_Detail:"{product_detail}",Ingredients:"{Ingredients}",Nutritional_information:"{Nutritional_information_json}",Allergen_warnings:"{Allergen_warnings}",Claims:"{Claims}",Endorsements:"{Endorsements}",Product_Image:"{img_link}",Product_origin:""}}

								$("#reward_{idx}").on("click", function(e){{
									e.preventDefault();
										$.ajax({{
										url: 'http://localhost:5000/reward',
										method: 'POST',
										headers: {{
											'Content-Type':'application/json'
										}},
										dataType: 'json',
										data: JSON.stringify(product_data_{idx})
										}});
								}});
								$("#feedback_{idx}").on("click", function(e){{
									e.preventDefault();
										$.ajax({{
										url: 'http://localhost:5000/feedback',
										method: 'POST',
										headers: {{
											'Content-Type':'application/json'
										}},
										dataType: 'json',
										data: JSON.stringify(product_data_{idx}),
										success: function(){{
											alert('Thank you for your feedback of product');
										}},
										error: function(){{
											alert('Thank you for your feedback of product [Error]');
										}}
										}});
								}});
							-->
							</script>

						'''.format(idx= idx, product_link=col1, title=col2, img_link=col3, price=col4, volume=col5, availability=availability, availability_color=availability_color, category_html=category_html, product_detail=col7, Ingredients=col8, Nutritional_information=col9, Nutritional_information_json = col9_for_Json, Allergen_warnings=col10, Claims=col11, Endorsements=col12, product_origin=col13, category_list = col6)


				# complate html tag
				PRODUCT_CARD += '</body>'

				# to display whole HTML as a single element 
				stc.html(PRODUCT_CARD, height=9000)

			except Exception as e:
				print(e)
				pass

	elif choice == "Scan receipt":
		# init variable image_arr
		image_arr = None
		st.subheader("Scan your receipt")
		image_file = st.file_uploader("Upload receipt image file", type=['jpg', 'png', 'jpeg'])
		if image_file is not None:
			# folder public_receipt_images contains all images from public upload
			if not os.path.exists("public_receipt_images"):
				os.makedirs("public_receipt_images")
			path = os.path.join("public_receipt_images", image_file.name)
			if_save_image = save_image(image_file)
			if if_save_image == 1:
				st.warning("File size is too large. Try another file with lower size.")
			elif if_save_image == 0:
				
				# display receipt
				try:
					# st.image(image_file, use_column_width=True)
					image_arr = cv2.imread(path, 0)
				except Exception as e:
				 	st.error(f"Error {e} - wrong format of the file. Try another .jpg file.")
			else:
				st.error("Unknown error")
		else:
			if st.button("Try test file"):
				# st.image("1.jpeg", use_column_width=True)
				image_file = "1.jpeg"
				image_arr = cv2.imread(image_file, 0)

		if image_arr is not None:
			# one function call to access everything
			output_score, image = scorecard_obj.get_score_from_receipt(image_arr, USER_PREFERENCE_TEXT= my_preference)
			st.write("Scanned image")
			st.image(image, use_column_width=True)
			print("output_score", output_score)
			#st.text(output_score)

			progress_bar = st.progress(0)

			# add animation of fill
			for i in range(output_score):
				# Update progress bar upto output score.
				progress_bar.progress(i + 1)
			
			# display score 
			SCORE_TITLE = """
			<div style="background-color:#464e5e;padding:10px;border-radius:10px">
			<h1 style="color:white;text-align:center;">{output_score} %</h1>
			<h3 style="color:white;text-align:center;"> is your shopping score </h3>
			</div>
			""".format(output_score= output_score)

			st.balloons()
			stc.html(SCORE_TITLE)

@st.cache(suppress_st_warning=True, allow_output_mutation=False)  
def start_RL_engine():
	# start reinforcement_learning_engine if not started
	reinforcement_engine_started = True
	import subprocess
	subprocess.Popen(['python', 'reinforcement_engine.py'], close_fds=True)

# main function
if __name__ == '__main__':
	recommendation_engine_gui()

	reinforcement_learning_enable = True

	if reinforcement_learning_enable:
		start_RL_engine()
