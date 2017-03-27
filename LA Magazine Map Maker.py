import os  # to allow directory changes, etc
import csv  # to allow loading the CSV file
import time  # to allow sleeps while geocoding
from collections import defaultdict  # easier dictionary to work with
import googlemaps  # the google maps API
import requests  # I have no idea what this does
import pickle  # to allow loading of a dictionary
import json  # to allow loading the API

__author__ = 'finn'
__project__ = 'Map the location of the LA Magazine Los Angeles Restaurants'

"""
This file takes a dictionary of the restaurants of LA Magazine's 100 most iconic dishes in Los Angeles and uses Google
Maps to make a static image with red pins for restaurants with dishes that haven't been tried and green flags for those
restaurants in which all the dished have been tried.
"""


class MapMaker:
    def __init__(self):
        if os.path.exists("locations.pkl"):
            self.locations = self.unpickle_dict()
        elif os.path.exists("LAMag restaurants.csv"):
            self.locations = self.file_reader()  # dictionary of all the restaurants
        else:
            print "Warning, I did not find either the pickle or the CSV file."

        # dictionary with the location of 1410 S. Barrington Ave, Los Angeles, CA 90025
        self.home = {u'lat': 34.0459854, u'lng': -118.4575366}
        self.full_url = "https://maps.googleapis.com/maps/api/staticmap?"  # the beginning of the static map URL

        with open("../credentials.json", "r") as keyfile:
            temp_key = json.load(keyfile)
        self.gmaps = googlemaps.Client(key=temp_key["gmap_key"])  # API access to google maps


    def file_reader(self):
        """reads in a file assuming the formatting created during data acquisition"""
        os.chdir('/python/LAMag')
        file_dict = defaultdict(lambda: defaultdict(dict))
        with open('LAMag restaurants.csv', 'rU') as data_file:
            reader = csv.reader(data_file)
            row_num = 0  # start the row number counter
            for row in reader:
                if row_num <= 1:
                    pass
                else:
                    if row[2] not in file_dict:
                        # if the restaurant doesn't exist yet, create it
                        file_dict[row[2]]["number"] = [int(row[0])]  # number on the LA Mag list
                        file_dict[row[2]]["items"][row[1]] = {}
                        file_dict[row[2]]["items"][row[1]]["Had?"] = bool(row[3])  # have you had the item?
                        # a flag for if you do no want it
                        file_dict[row[2]]["items"][row[1]]["Do not want"] = bool(row[4])
                        # flag for if you cannot eat it
                        file_dict[row[2]]["items"][row[1]]["Can not have"] = bool(row[5])
                    else:  # if it does exist, append the new number and add the item
                        file_dict[row[2]]["number"].append(int(row[0]))  # PyCharm gives a weak error, but this works
                        file_dict[row[2]]["items"][row[1]] = {}
                        file_dict[row[2]]["items"][row[1]]["Had?"] = bool(row[3])  # have you had the item?
                        # a flag for if you do no want it
                        file_dict[row[2]]["items"][row[1]]["Do not want"] = bool(row[4])
                        # flag for if you cannot eat it
                        file_dict[row[2]]["items"][row[1]]["Can not have"] = bool(row[5])
                row_num += 1  # increment the row number
        return dict(file_dict)  # change to a common dictionary

    def pickle_dict(self):
        with open("locations.pkl", "wb") as f:
            pickle.dump(self.locations, f)

    def unpickle_dict(self):
        with open("locations.pkl", "r") as f:
            retrieved = pickle.load(f)
        return retrieved

    def get_location(self, rest_name):
        temp_loc = self.gmaps.places(query=rest_name + " restaurant, Los Angeles County", location=self.home)

        locs = [temp_loc["results"][ii]["geometry"]["location"] for ii in range(len(temp_loc["results"]))]

        print rest_name + ": " + str(len(locs))

        return locs

    def parse_dictionary(self):

        counter = 0  # initialize a counter
        for key in self.locations:
            if not self.locations[key]["locations"]:  # check if the location info does not exist
                # if the location info does not exist, fetch it from google maps
                self.locations[key]["locations"] = self.get_location(key)
                counter += 1  # increase the counter by one, we only care if we access google maps
            time.sleep(1)

    def create_map(self):
        """
        Makes a static map of all of the locations in the LA Magazine article.
        Based on the example shown here:
        http://www.manejandodatos.es/2015/07/generating-statics-maps-with-google-maps-and-python/

        :return:
        """
        base_url = "center=34.1,-118.30&zoom=11&scale=2&size=640x640&maptype=roadmap"  # general map information
        # same as above but focuses on the Fairfax area
        #base_url = "center=34.0748311, -118.3732182&zoom=15&scale=2&size=640x640&maptype=roadmap"
        # how to add markers to base_url
        # &markers=color:green|label:1|34.1,-118.36&markers=color:blue|label:2|34.1,-118.38

        # add the base url to the full url
        self.full_url += base_url

        for key in self.locations:
            self.full_url += self.single_rest_marker_string(key)

        sesh = requests.Session()
        r = sesh.get(self.full_url)
        with open('the_image.png', 'wb') as f:
            f.write(r.content)
            f.close()

    def single_rest_marker_string(self, key):
        """
        The function puts together the marker url for a single restaurant
        :param key: the name of a restaurant key in the dictionary
        :return:
        """

        url_holder = ''

        for j in range(len(self.locations[key]["locations"])):
            had_it = True  # default state of had_it is true, so when multiplied by false it becomes false
            tmp_dict = defaultdict(dict)
            tmp_dict["number"] = self.locations[key]["number"]
            tmp_dict["lat"] = self.locations[key]["locations"][j]["lat"]
            tmp_dict["lng"] = self.locations[key]["locations"][j]["lng"]
            for item in self.locations[key]["items"].keys():
                had_it *= self.locations[key]["items"][item]["Had?"]
            # print key + ": " + str(bool(had_it))
            if not had_it:  # if you have not had all the items, use a red marker
                tmp_mark = "&markers=color:red|label:+|{lat},{lng}".format(**tmp_dict)
            else:  # if you have had all the items, use a green marker
                tmp_mark = "&markers=color:green|label:|{lat},{lng}".format(**tmp_dict)
            url_holder += tmp_mark

        return url_holder
