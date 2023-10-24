import json
import os
from datetime import datetime, time, timedelta
from flask import Flask, request, jsonify
import mysql.connector

# Retrieve Azure MySQL connection details from environment variables
azure_mysql_host = os.environ.get("AZURE_MYSQL_HOST")
azure_mysql_password = os.environ.get("AZURE_MYSQL_PASSWORD")
azure_mysql_user = os.environ.get("AZURE_MYSQL_USER")

class TimedeltaEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        return super().default(obj)

class Restaurant:
    def __init__(self, id, name, style, address, openHour, closeHour, vegetarian, delivery):
        self.id = id
        self.name = name
        self.style = style
        self.address = address
        self.openHour = self.get_time_from_string(openHour)
        self.closeHour = self.get_time_from_string(closeHour)
        self.vegetarian = vegetarian
        self.delivery = delivery
    
    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "style": self.style,
            "address": self.address,
            "openHour": self.openHour.strftime('%H:%M'),
            "closeHour": self.closeHour.strftime('%H:%M'),
            "vegetarian": self.vegetarian,
            "delivery": self.delivery
        }
    
    def get_time_from_string(self, time_str):
        if isinstance(time_str, str):
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        elif isinstance(time_str, timedelta):
            # Convert timedelta to time
            total_seconds = int(time_str.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes = remainder // 60
            return time(hours, minutes)
        else:
            raise ValueError("Invalid time format")

class RestaurantRecommendationSystemAPI:
    def __init__(self, db):
        self.db = db

    def is_open(self, restaurant):
        current_time = datetime.now().time()
        return restaurant.openHour <= current_time <= restaurant.closeHour

    def get_recommendation(self, criteria):
        conn = mysql.connector.connect(host=azure_mysql_host, user=azure_mysql_user, password=azure_mysql_password, db='restaurants')
        cur = conn.cursor()

        query = """
            SELECT *
            FROM restaurants
            WHERE 
        """
        attributes_list = ["id", "name", "style", "address", "openHour", "closeHour", "vegetarian", "delivery"]
        
        for key, value in criteria.items():
            if key not in attributes_list:
                return
            query += f" {key} = '{value}' AND"

        query = query[:-4]
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()

        restaurants = []
        for result in results:
            id, name, style, address, openHour, closeHour, vegetarian, delivery = result
            restaurant = Restaurant(id, name, style, address, openHour, closeHour, vegetarian, delivery)
            if self.is_open(restaurant):
                restaurants.append(restaurant.to_json())

        return restaurants

# Create a MySQL connection without specifying a database
db = mysql.connector.connect(host=azure_mysql_host, user=azure_mysql_user, password=azure_mysql_password)
cursor = db.cursor()

# Drop the 'restaurants' database if it already exists
drop_database_query = "DROP DATABASE IF EXISTS restaurants;"
cursor.execute(drop_database_query)

# Create the 'restaurants' database
create_database_query = "CREATE DATABASE restaurants;"
cursor.execute(create_database_query)

# Switch to the 'restaurants' database
use_database_query = "USE restaurants;"
cursor.execute(use_database_query)

create_table_query = """
CREATE TABLE IF NOT EXISTS restaurants (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  style VARCHAR(255) NOT NULL,
  address VARCHAR(255) NOT NULL,
  openHour TIME NOT NULL,
  closeHour TIME NOT NULL,
  vegetarian BOOL NOT NULL,
  delivery BOOL NOT NULL,
  PRIMARY KEY (id)
);
"""

# Check if the 'restaurants' table exists before attempting to create it
cursor.execute(create_table_query)

# Reconnect to the 'restaurants' database
db = mysql.connector.connect(host=azure_mysql_host, user=azure_mysql_user, password=azure_mysql_password, database='restaurants')
cursor = db.cursor()

# Insert data into the database
insert_query = """
INSERT INTO restaurants (name, style, address, openHour, closeHour, vegetarian, delivery) VALUES
  ('Pizza Hut', 'Italian', 'Wherever Street 99, Somewhere', '09:00', '23:00', TRUE, TRUE),
  ('Dominos', 'Italian', 'Any Street 100, Somewhere', '10:00', '22:00', TRUE, TRUE),
  ('Subway', 'American', 'Random Street 101, Somewhere', '11:00', '21:00', TRUE, TRUE),
  ('McDonald''s', 'American', 'Random Street 102, Somewhere', '12:00', '20:00', FALSE, TRUE),
  ('Burger King', 'American', 'Random Street 103, Somewhere', '13:00', '19:00', FALSE, TRUE),
  ('KFC', 'American', 'Random Street 104, Somewhere', '14:00', '18:00', FALSE, TRUE),
  ('Starbucks', 'Coffee', 'Random Street 105, Somewhere', '15:00', '17:00', TRUE, TRUE),
  ('Costa Coffee', 'Coffee', 'Random Street 106, Somewhere', '16:00', '16:00', TRUE, TRUE),
  ('Indian Curry House', 'Indian', 'Random Street 107, Somewhere', '17:00', '15:00', TRUE, TRUE),
  ('Chinese Takeaway', 'Chinese', 'Random Street 108, Somewhere', '18:00', '14:00', TRUE, TRUE),
  ('Mexican Restaurant', 'Mexican', 'Random Street 109, Somewhere', '19:00', '13:00', TRUE, TRUE),
  ('Thai Restaurant', 'Thai', 'Random Street 110, Somewhere', '20:00', '12:00', TRUE, TRUE),
  ('Japanese Restaurant', 'Japanese', 'Random Street 111, Somewhere', '21:00', '11:00', TRUE, TRUE),
  ('Korean Restaurant', 'Korean', 'Random Street 112, Somewhere', '22:00', '10:00', TRUE, TRUE),
  ('Vietnamese Restaurant', 'Vietnamese', 'Random Street 113, Somewhere', '23:00', '09:00', TRUE, TRUE),
  ('Vegan Restaurant', 'Vegan', 'Random Street 114, Somewhere', '00:00', '08:00', TRUE, TRUE),
  ('Gluten-Free Restaurant', 'Gluten-Free', 'Random Street 115, Somewhere', '01:00', '07:00', TRUE, TRUE),
  ('Halal Restaurant', 'Halal', 'Random Street 116, Somewhere', '02:00', '06:00', TRUE, TRUE),
  ('Kosher Restaurant', 'Kosher', 'Random Street 117, Somewhere', '03:00', '05:00', TRUE, TRUE),
  ('24-Hour Restaurant', '24-Hour', 'Random Street 118, Somewhere', '04:00', '04:00', TRUE, TRUE);
"""

cursor.execute(insert_query)
db.commit()
recommendation_system = RestaurantRecommendationSystemAPI(db)

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1><center>Hello! Welcome to Restaurants Listing Sample App with API, hosted on Azure App Services. 🙏🏻</center></h1>"

@app.route("/api/health", methods=["GET"])
def health_check():
    return "<h1><center>OK, Your app is running fine. 😄 </center></h1>"

@app.route("/api/recommendation", methods=["GET"])
def get_recommendation():
    # Get the criteria from the request
    criteria = request.args

    if not criteria:
        return "<h1><center> No arguments/parameters passed.</center></h1>"

    # Get the recommendation from the restaurant recommendation system
    recommendations = recommendation_system.get_recommendation(criteria)

    formatted_recommendations = []

    for restaurant in recommendations:
        formatted_recommendations.append({
            "name": restaurant['name'],
            "id": restaurant['id'],
            "style": restaurant['style'],
            "address": restaurant['address'],
            "openHour": restaurant['openHour'],
            "closeHour": restaurant['closeHour'],
            "vegetarian": "yes" if restaurant['vegetarian'] == 1 else "no",
            "delivery": "yes" if restaurant['delivery'] == 1 else "no"
        })
    
    if not formatted_recommendations:
        return "<h1><center> No Restaurant for above criteria is open now or Invalid Query...☹️</center></h1>"
    
    return jsonify(formatted_recommendations)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
