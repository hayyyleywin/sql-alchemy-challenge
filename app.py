import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from flask import Flask, jsonify


#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)
Base.classes.keys()

# Create our session (link) from Python to the DB
session = Session(engine)

Measurement = Base.classes.measurement
Station = Base.classes.station

# Calculate the date one year from the last date in data set.
first_date=session.query(Measurement.date).order_by(Measurement.date).first().date

# Find the most recent date in the data set.
recent_date=session.query(Measurement.date).order_by(Measurement.date.desc()).first()

#extract string from query object
recent_date = list(np.ravel(recent_date))[0]

#convert date string to datetime object
recent_date = dt.datetime.strptime(recent_date, '%Y-%m-%d')

# to get the date before 12 months from recent date, 
date_from_12months= recent_date - dt.timedelta(days = 365)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)

@app.route("/")
def welcome():
    
    session = Session(engine)
    
    """List all available api routes."""
    return (
        f"Welcome to the HAWAI Surf Up!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/startDate<br/>"
        f"/api/v1.0/<startDate>/<endDate>"
    )

#######################################################################################
#Convert the query to a dictionary using date as the key and prcp as the value.
#Return the JSON representation of your dictionary.
########################################################################################


@app.route("/api/v1.0/precipitation")
def precipitation():
    
    session = Session(engine)

    Result= session.query(Measurement.date, Measurement.prcp).\
    filter(Measurement.date >= date_from_12months).\
    group_by(Measurement.date).all()

    session.close()

 # Create a dictionary from the row data and append to a list of results
    dic_prcp_date = []
    for date, prcp in  Result:
        data = {}
        data['date'] = date
        data['prcp'] = prcp
        dic_prcp_date.append(data)

    return jsonify(dic_prcp_date)



#######################################################################################
#Return a JSON list of stations from the dataset.
########################################################################################

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    
    results = session.query(Station.name, Station.station).all()

    session.close()
    
    #create dictionary for JSON
    station_list = []
    for result in results:
        data = {}
        data['name'] = result[0]
        data['station'] = result[1]
        station_list.append( data)
    return jsonify(station_list)
 
    
    
    
    
#######################################################################################
#Query the dates and temperature observations of the most active station for the last year of data.
#Return a JSON list of temperature observations (TOBS) for the previous year.
########################################################################################    

@app.route("/api/v1.0/tobs")
def temperature_tobs():
    
    session = Session(engine)

# Design a query to find the most active stations
    Count_by_Station= session.query(Measurement.station, func.count(Measurement.station)).\
                    group_by(Measurement.station).\
                    order_by(func.count(Measurement.station).desc()).all()
    
# Using the most active station id from the previous query, calculate the lowest, highest, and average temperature.
    Best_station = Count_by_Station[0][0]
    session.query(func.min(Measurement.tobs), 
                  func.avg(Measurement.tobs), 
                  func.max(Measurement.tobs)).\
                filter(Measurement.station == Best_station).all()
        
# Using the most active station id
    results = session.query(Station.name, Measurement.date, Measurement.tobs).\
    filter(Measurement.station == Best_station).\
    filter(Measurement.date >= date_from_12months).all()

    
    session.close()
    
    #use dictionary, create json
    tobs_list = []
    for result in results:
        row = {}
        row["Date"] = result[1]
        row["Station"] = result[0]
        row["Temp"] = int(result[2])
        tobs_list.append(row)

    return jsonify(tobs_list)


  
#######################################################################################
#Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.

#When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.

#When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive.
########################################################################################      

@app.route("/api/v1.0/startDate")
def start(startDate):
    
    val = [Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    
    results =  (session.query(*val)
                       .filter(func.strftime("%Y-%m-%d", Measurement.date) >= startDate)
                       .group_by(Measurement.date)
                       .all())
    
    dates = []                       
    for result in results:
        date_dict = {}
        date_dict["Date"] = result[0]
        date_dict["Low Temp"] = result[1]
        date_dict["Avg Temp"] = result[2]
        date_dict["High Temp"] = result[3]
        dates.append(date_dict)
    return jsonify(dates)
    

if __name__ == "__main__":
    app.run(debug=True)