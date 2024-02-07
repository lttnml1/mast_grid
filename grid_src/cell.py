#!/usr/bin/env python
#NATIVE PYTHON IMPORTS
import math
from enum import Enum

#INSTALLED PACKAGE IMPORTS
from geopy.point import Point
from geopy.distance import distance
from global_land_mask import globe

#IMPORTS FROM THIS PACAKGE

class LandorWater(Enum):
    LAND = 0
    WATER = 1

class Cell:
    def __init__(self, top_left: Point, width: int, height: int, coordinate):
        self.top_left = top_left
        self.width = width
        self.height = height
        self.coordinate = coordinate
        self.i = coordinate[0]
        self.j = coordinate[1]
        self.compute_corners()
        self.land_or_water()
        self.poly_coords = [
            [self.top_left.latitude,self.top_left.longitude],
            [self.top_right.latitude,self.top_right.longitude],
            [self.bottom_right.latitude,self.bottom_right.longitude],
            [self.bottom_left.latitude,self.bottom_left.longitude],
            [self.top_left.latitude,self.top_left.longitude]
        ]
        self.of_interest = False
    
    def compute_corners(self):
        corner_distance = math.sqrt((self.width/2)**2 + (self.height/2)**2)
        self.center = distance(kilometers = corner_distance).destination(point=self.top_left,bearing=180-math.degrees(math.atan(self.width/self.height)))
        self.top_right = distance(kilometers = corner_distance).destination(point=self.center,bearing=math.degrees(math.atan(self.width/self.height)))
        self.bottom_right = distance(kilometers = corner_distance).destination(point=self.center,bearing=180-math.degrees(math.atan(self.width/self.height)))
        self.bottom_left = distance(kilometers = corner_distance).destination(point=self.center,bearing=180+math.degrees(math.atan(self.width/self.height)))
    
    def land_or_water(self):
        land_counter = 0
        self.type = LandorWater.WATER
        sample_list = [self.center,self.top_left,self.top_right,self.bottom_left,self.bottom_right]
        for sample in sample_list:
            if(globe.is_land(sample.latitude,sample.longitude)):
                land_counter+=1
        if(land_counter > 1):#len(sample_list)/2):
            self.type = LandorWater.LAND
    
    def set_of_interest(self, of_interest = True):
        self.of_interest = of_interest