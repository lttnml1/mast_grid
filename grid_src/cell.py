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
    LAND = 1
    WATER = 2

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
    
    def compute_corners(self):
        corner_distance = math.sqrt(self.width**2 + self.height**2)
        self.center = distance(kilometers = corner_distance).destination(point=self.top_left,bearing=135)
        self.top_right = distance(kilometers = corner_distance).destination(point=self.center,bearing=45)
        self.bottom_right = distance(kilometers = corner_distance).destination(point=self.center,bearing=135)
        self.bottom_left = distance(kilometers = corner_distance).destination(point=self.center,bearing=225)
    
    def land_or_water(self):
        land_counter = 0
        self.type = LandorWater.WATER
        sample_list = [self.center,self.top_left,self.top_right,self.bottom_left,self.bottom_right]
        for sample in sample_list:
            if(globe.is_land(sample.latitude,sample.longitude)):
                land_counter+=1
        if(land_counter > len(sample_list)/2):
            self.type = LandorWater.LAND   
