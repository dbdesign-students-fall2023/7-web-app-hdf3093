#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, make_response
from markupsafe import escape
import pymongo
import datetime
from bson.objectid import ObjectId
import os
import subprocess
# instantiate the app
app = Flask(__name__)

# load credentials and configuration options from .env file
# if you do not yet have a file named .env, make one based on the template in env.example


import credentials
config = credentials.get()

# turn on debugging if in development mode
if config['FLASK_ENV'] == 'development':
    # turn on debugging, if in development
    app.debug = True # debug mnode

# make one persistent connection to the database
connection = pymongo.MongoClient(config['class-mongodb.cims.nyu'], 27017, 
                                username=config['hdf3093'],
                                password=config['LBRVB3AJ'],
                                authSource=config['bladee'])
db = connection[config['bladee']] # store a reference to the database



# set up the routes

@app.route('/')
def home():
    """
    Route for the home page
    """
    return render_template('index.html')


@app.route('/read')
def read():
    """
    Route for GET requests to the read page.
    Displays some information for the user with links to other pages.
    """
    docs = db.albums.find({}).sort("release_date", -1)
    return render_template('read.html', docs=docs)



@app.route('/create')
def create():
    """
    Route for GET requests to the create page.
    Displays a form users can fill out to create a new document.
    """
    return render_template('create.html') # render the create template


@app.route('/create', methods=['POST'])
def create_post():
    """
    Route for POST requests to the create page.
    Accepts the form submission data for a new review and saves the review to the database.
    """
    username = request.form['username']
    rating = int(request.form['rating'])
    comment = request.form['comment']
    album_title = request.form['album_title']

    # Find selected album in the database based on the user input
    album = db.bladee.find_one({"title": album_title})

    if album:
        # Create a new review document with the data the user entered
        review = {
            "username": username,
            "rating": rating,
            "comment": comment,
        }

        # Append the new review to the reviews list of the selected album
        db.bladee.update_one({"title": album_title}, {"$push": {"reviews": review}})

    return redirect(url_for('read'))  



@app.route('/edit/<mongoid>')
def edit(mongoid):
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.
    """
    doc = db.bladee.find_one({"_id": ObjectId(mongoid)})
    return render_template('edit.html', mongoid=mongoid, doc=doc) # render the edit template


@app.route('/edit/<mongoid>', methods=['POST'])
def edit_post(mongoid):
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    """
    username = request.form['username']
    rating = int(request.form['rating'])
    comment = request.form['comment']
    album_title = request.form['album_title']

    # Find the document by its _id
    doc = db.bladee.find_one({"_id": ObjectId(mongoid)})

    # Update the review information
    review_to_update = next((review for review in doc['reviews'] if review['album_title'] == album_title), None)

    if review_to_update:
        # Define the review dictionary with the updated data
        review = {
            "username": username,
            "rating": rating,
            "comment": comment,
            "album_title": album_title  # Make sure to include this line
        }

        # Update the specific review within the reviews array
        db.bladee.update_one(
            {"_id": ObjectId(mongoid), "reviews.album_title": album_title},
            {"$set": {"reviews.$": review}}
        )

    return redirect(url_for('read'))



@app.route('/delete/<mongoid>')
def delete(mongoid):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.
    """
    db.bladee.delete_one({"_id": ObjectId(mongoid)})
    return redirect(url_for('read')) # tell the web browser to make a request for the /read route.

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub can be configured such that each time a push is made to a repository, GitHub will make a request to a particular web URL... this is called a webhook.
    This function is set up such that if the /webhook route is requested, Python will execute a git pull command from the command line to update this app's codebase.
    You will need to configure your own repository to have a webhook that requests this route in GitHub's settings.
    Note that this webhook does do any verification that the request is coming from GitHub... this should be added in a production environment.
    """
    # run a git pull command
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    pull_output = process.communicate()[0]
    # pull_output = str(pull_output).strip() # remove whitespace
    process = subprocess.Popen(["chmod", "a+x", "flask.cgi"], stdout=subprocess.PIPE)
    chmod_output = process.communicate()[0]
    # send a success response
    response = make_response('output: {}'.format(pull_output), 200)
    response.mimetype = "text/plain"
    return response

@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template('error.html', error=e) # render the edit template


if __name__ == "__main__":
    #import logging
    #logging.basicConfig(filename='/home/ak8257/error.log',level=logging.DEBUG)
    app.run(debug = True)



