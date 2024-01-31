#!/usr/bin/env python
#NATIVE PYTHON IMPORTS
import json
import math

#INSTALLED PACKAGE IMPORTS
from geopy.point import Point
from geopy.distance import distance
import folium
from shapely import Polygon
from shapely import Point as ShapelyPoint

#IMPORTS FROM THIS PACAKGE
from grid_src.cell import Cell

folium_colors = ['red','blue','green','purple','orange','darkred','lightred','beige','darkblue','darkgreen','cadetblue','darkpurple','white','pink','lightblue','lightgreen','gray','black','lightgray']

"""
The grid is an overlay of the map with center at the starting point of the Blue Frigate
Rows/Columns are zero-based
Rows increase to the South
Columns increase to the North

e.g., for a 5x5 grid

+-----+-----+-----+-----+-----+
|(0,0)|(0,1)|(0,2)|(0,3)|(0,4)|
+-----+-----+-----+-----+-----+
|(1,0)|(1,1)|(1,2)|(1,3)|(1,4)|
+-----+-----+-----+-----+-----+
|(2,0)|(2,1)|(2,2)|(2,3)|(2,4)|
|     |     |BLUE |     |     |
|     |     |FFG  |     |     |
+-----+-----+-----+-----+-----+
|(3,0)|(3,1)|(3,2)|(3,3)|(3,4)|
+-----+-----+-----+-----+-----+
|(4,0)|(4,1)|(4,2)|(4,3)|(4,4)|
+-----+-----+-----+-----+-----+

"""

class Grid:
    def __init__(self, scenario_file: str, grid_width: int = 11, grid_height: int = 11):
        self.scenario_file = scenario_file
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.parse_scenario_file()

        #the distance the grid should extend up/down/left/right from center **in km**
        self.max_distance_from_center = (self.max_uxv_speed * self.max_time)/1000
        self.build_grid()
    
    def plot(self):
        #define a new map at the center point
        map = folium.Map(location = [self.center.latitude,self.center.longitude], zoom_start = 6)

        for row in self.grid:
            for cell in row:
                folium.Polygon(cell.poly_coords,color="darkred",weight=1,fill=False).add_to(map)
                #folium.Polygon(cell.poly_coords,color="darkred",weight=1,fill=False, tooltip=folium.Tooltip(text=f"{cell.coordinate}",permanent=True)).add_to(map)

       
        #plot the center point
        folium.CircleMarker([self.center.latitude,self.center.longitude],radius=20,color='black',fill=False,tooltip=folium.Tooltip(text="START",permanent=True)).add_to(map)

        #plot edges of graph
        folium.CircleMarker([self.grid_top_left.latitude,self.grid_top_left.longitude],radius=10,color='blue',fill=False,tooltip=folium.Tooltip(text="TopLeft",permanent=True)).add_to(map)
        folium.CircleMarker([self.grid_top_right.latitude,self.grid_top_right.longitude],radius=10,color='green',fill=False,tooltip=folium.Tooltip(text="TopRight",permanent=True)).add_to(map)
        folium.CircleMarker([self.grid_bottom_right.latitude,self.grid_bottom_right.longitude],radius=10,color='orange',fill=False,tooltip=folium.Tooltip(text="BottomRight",permanent=True)).add_to(map)
        folium.CircleMarker([self.grid_bottom_left.latitude,self.grid_bottom_left.longitude],radius=10,color='pink',fill=False,tooltip=folium.Tooltip(text="BottomLeft",permanent=True)).add_to(map)
        """
        #first plot rows (east-west lines)
        left_point = self.grid_top_left
        right_point = self.grid_top_right
        for i in range(self.grid_height+1):
            folium.PolyLine([[left_point.latitude,left_point.longitude],[right_point.latitude,right_point.longitude]],color='darkred',weight=1).add_to(map)
            left_point = distance(kilometers=self.cell_height).destination(point=left_point,bearing=180)
            right_point = distance(kilometers=self.cell_height).destination(point=right_point,bearing=180)

        #second plot columns (north-south lines)
        top_point = self.grid_top_left
        bottom_point = self.grid_bottom_left
        for i in range(self.grid_width+1):
            folium.PolyLine([[top_point.latitude,top_point.longitude],[bottom_point.latitude,bottom_point.longitude]],color='darkblue',weight=1).add_to(map)
            top_point = distance(kilometers=self.cell_width).destination(point=top_point,bearing=90)
            bottom_point = distance(kilometers=self.cell_width).destination(point=bottom_point,bearing=90)
        """
        #display the map
        display(map)
    
    def parse_scenario_file(self,print_json=False):
        self.scenario_json = json.load(open(self.scenario_file))
        if(print_json):
            print(json.dumps(self.scenario_json,indent=4))

        #find initial location of BLUE FFG
        initial_blue_loc = self.scenario_json["Multi-Run"]["Agents"][0]["Platform"]["Initial Location"]["Position"]
        self.center = Point(latitude=initial_blue_loc["Lat"]["Angle"],longitude=initial_blue_loc["Lon"]["Angle"])

        #find max UxV speed (m/s)
        uxv_speeds = self.scenario_json["Multi-Run"]["Agents"][0]["Subsystems"][1]["Jam Conditions"][0]["Detectors"][0]
        self.max_uxv_speed = uxv_speeds["UAV Speed"]["Speed"]
        if(uxv_speeds["USV Speed"]["Speed"] > self.max_uxv_speed):
            self.max_uxv_speed = uxv_speeds["USV Speed"]["Speed"]

        #find max scenario execution time
        self.max_time = self.scenario_json["Multi-Run"]["Max Seconds"]
    
    def build_grid(self):
        self.grid_top_left = distance(kilometers = self.max_distance_from_center * math.sqrt(2)).destination(point=self.center,bearing=315)
        self.grid_top_right = distance(kilometers = self.max_distance_from_center * math.sqrt(2)).destination(point=self.center,bearing=45)
        self.grid_bottom_left = distance(kilometers = self.max_distance_from_center * math.sqrt(2)).destination(point=self.center,bearing=225)
        self.grid_bottom_right = distance(kilometers = self.max_distance_from_center * math.sqrt(2)).destination(point=self.center,bearing=135)

        #cell_height is the North/South distance of a grid cell
        self.cell_height = distance(self.grid_top_left,self.grid_bottom_left).kilometers/self.grid_height

        #cell_width is the Easy/West distance of a grid cell
        self.cell_width = distance(self.grid_top_left,self.grid_top_right).kilometers/self.grid_width

        grid = []
        row_top_left = self.grid_top_left
        for i in range(self.grid_height):
            row = []
            cell_top_left = row_top_left
            for j in range(self.grid_width):
                c = Cell(cell_top_left,self.cell_width,self.cell_height,(i,j))
                row.append(c)
                cell_top_left = distance(kilometers=self.cell_width).destination(point=cell_top_left,bearing=90)
            grid.append(row)
            row_top_left = distance(kilometers=self.cell_height).destination(point=row_top_left,bearing=180)
        self.grid = grid

    def convert_index_to_latlong(self, i: int, j: int) -> Point:
        for row in self.grid:
            for cell in row:
                if(cell.i == i and cell.j == j):
                    return cell.center.format_decimal()

    def convert_latlong_to_index(self, lat: float, lon: float):
        point = ShapelyPoint(lat,lon)
        for row in self.grid:
            for cell in row:
                polygon = Polygon(cell.poly_coords)
                if(polygon.contains(point)):
                    return (cell.i, cell.j)