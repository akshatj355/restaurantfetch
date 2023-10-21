import json
from datetime import datetime, time, timedelta
from flask import Flask, request, jsonify
import mysql.connector

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

class RestaurantRecommendationSystem:
    def __init__(self, db):
        self.db = db

    def is_open(self, restaurant):
        current_time = datetime.now().time()
        return restaurant.openHour <= current_time <= restaurant.closeHour

    def get_recommendation(self, criteria):
        conn = mysql.connector.connect(host='localhost', user='root', password='Akshatj@355', db='restaurants')
        cur = conn.cursor()

        query = """
            SELECT *
            FROM restaurants
            WHERE 
        """

        for key, value in criteria.items():
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

db = mysql.connector.connect(host='localhost', user='root', password='Akshatj@355', db='restaurants')
recommendation_system = RestaurantRecommendationSystem(db)

app = Flask(__name__)

@app.route("/api/health", methods=["GET"])
def health_check():
    return "OK"

@app.route("/api/recommendation", methods=["GET"])
def get_recommendation():
    # Get the criteria from the request
    criteria = request.args

    if not criteria:
        return "No arguments/parameters passed."

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

    return jsonify(formatted_recommendations)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
