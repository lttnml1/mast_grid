#!/usr/bin/env python
#NATIVE PYTHON IMPORTS
import json
import math

#INSTALLED PACKAGE IMPORTS
from geopy.point import Point
from geopy.distance import distance
from geopy import units
import folium
from shapely import Polygon
from shapely import Point as ShapelyPoint
import numpy as np

#IMPORTS FROM THIS PACAKGE
from grid_src.cell import Cell, LandorWater

folium_colors = ['red','blue','green','purple','orange','darkred','lightred','beige','darkblue','darkgreen','cadetblue','darkpurple','white','pink','lightblue','lightgreen','gray','black','lightgray']

"""
The grid is an overlay of the map with center at the starting point of the Blue Frigate
Rows/Columns are zero-based
Rows increase to the South
Columns increase to the East

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
    def __init__(self, scenario_file: str, grid_width: int = 11, grid_height: int = 11, print_stats = False):
        self.scenario_file = scenario_file
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.parse_scenario_file()

        #the distance the grid should extend up/down/left/right from center **in km**
        self.max_distance_from_center = (self.max_uxv_speed * self.max_time)/1000
        self.build_grid(print_stats)
        self.determine_of_interest()
    
    def plot(self):
        #define a new map at the center point
        map = folium.Map(location = [self.grid_center.latitude,self.grid_center.longitude], zoom_start = 8)

        for row in self.grid:
            for cell in row:
                if(cell.type == LandorWater.LAND):
                    folium.Polygon(cell.poly_coords,color="darkred",weight=3,fill=False).add_to(map)
                else:
                    folium.Polygon(cell.poly_coords,color="blue",weight=1,fill=False).add_to(map)
                #folium.Polygon(cell.poly_coords,color="darkred",weight=1,fill=False, tooltip=folium.Tooltip(text=f"{cell.coordinate}",permanent=True)).add_to(map)


        #Plot BLUE initial location
        folium.CircleMarker([self.initial_blue_loc.latitude,self.initial_blue_loc.longitude],radius=10,color='blue',fill=False,tooltip=folium.Tooltip(text="BLUE FFG",permanent=True)).add_to(map)

        #Plot RED initial location
        folium.CircleMarker([self.red_loc.latitude,self.red_loc.longitude],radius=10,color='red',fill=False,tooltip=folium.Tooltip(text="RED FFG",permanent=True)).add_to(map)

        #Plot TAIs
        count = 0
        for area in self.areas_of_interest:
            folium.CircleMarker([area[0],area[1]],radius=10,color='orange',fill=False,tooltip=folium.Tooltip(text=f"TAI {count}",permanent=True)).add_to(map)
            count += 1
        
        """
        #plot the center point
        folium.CircleMarker([self.initial_blue_loc.latitude,self.initial_blue_loc.longitude],radius=20,color='black',fill=False,tooltip=folium.Tooltip(text="START",permanent=True)).add_to(map)

        #plot edges of graph
        folium.CircleMarker([self.grid_top_left.latitude,self.grid_top_left.longitude],radius=10,color='blue',fill=False,tooltip=folium.Tooltip(text="TopLeft",permanent=True)).add_to(map)
        folium.CircleMarker([self.grid_top_right.latitude,self.grid_top_right.longitude],radius=10,color='green',fill=False,tooltip=folium.Tooltip(text="TopRight",permanent=True)).add_to(map)
        folium.CircleMarker([self.grid_bottom_right.latitude,self.grid_bottom_right.longitude],radius=10,color='orange',fill=False,tooltip=folium.Tooltip(text="BottomRight",permanent=True)).add_to(map)
        folium.CircleMarker([self.grid_bottom_left.latitude,self.grid_bottom_left.longitude],radius=10,color='pink',fill=False,tooltip=folium.Tooltip(text="BottomLeft",permanent=True)).add_to(map)
        
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
    
    def parse_scenario_file(self,print_json=True):
        self.scenario_json = json.load(open(self.scenario_file))
        if(print_json):
            print(json.dumps(self.scenario_json,indent=4))

        #find initial location of BLUE FFG
        try:
            initial_blue_loc = self.scenario_json["Multi-Run"]["Agents"][0]["Platform"]["Initial Location"]["Position"]
            self.initial_blue_loc = Point(latitude=initial_blue_loc["Lat"]["Angle"],longitude=initial_blue_loc["Lon"]["Angle"])
        except KeyError:
            print("Error reading initial BLUE location from JSON")

        #find initial location for RED FFG
        try:
            initial_red_loc = self.scenario_json["Multi-Run"]["Agents"][1]["Platform"]["Initial Location"]["Position"]
            self.red_loc = Point(latitude=initial_red_loc["Lat"]["Angle"],longitude=initial_red_loc["Lon"]["Angle"])
        except KeyError:
            print("Error reading initial RED location from JSON")

        #find max UxV speed (m/s)
        try:
            uxv_info = self.scenario_json["Multi-Run"]["Agents"][0]["Subsystems"][1]["Jam Conditions"][0]["Detectors"][0]
            self.max_uxv_speed = uxv_info["UAV Speed"]["Speed"]
            if(uxv_info["USV Speed"]["Speed"] > self.max_uxv_speed):
                self.max_uxv_speed = uxv_info["USV Speed"]["Speed"]
        except KeyError:
            print("Error reading initial UxV speeds from JSON")

        #find number of UAVs and USVs
        try:
            self.num_uavs = uxv_info["Number of UAVs"]
            self.num_usvs = uxv_info["Number of USVs"]
        except KeyError:
            print("Error reading number of UxVs from JSON")

        #find maximum comms range
        try:
            self.max_comms_range = uxv_info["Maximum Comms Range"]["Distance"]
        except KeyError:
            print("Error reading maximum comms range from JSON")

        #find max scenario execution time
        try:
            self.max_time = self.scenario_json["Multi-Run"]["Max Seconds"]
        except KeyError:
            print("Error reading max scenario execution time from JSON")

        #find NAIs/LOIs
        NAIs = []
        LOIs = []
        try:
            AI = self.scenario_json["Multi-Run"]["Agents"][0]["Subsystems"][1]["Jam Conditions"][0]["Detectors"][0]
            NAI = AI["Named Area of Interest"]
            LOI = AI["Locations of Interest"]
            for area in NAI:
                NAIs.append([area["Lat"]["Angle"],area["Lon"]["Angle"]])
            for area in LOI:
                LOIs.append([area["Lat"]["Angle"],area["Lon"]["Angle"]])
        except KeyError:
            print("Error reading areas of interest from JSON")
        
        self.areas_of_interest = NAIs# + LOIs

        #find BLUE FFG/Virtual Leader Waypoints
        blue_wps = []
        try:
            for wp in self.scenario_json["Multi-Run"]["Agents"][0]["State Machines"][3]["States"][0]["State"]["Waypoints"]:
                blue_wps.append([wp["Lat"]["Angle"],wp["Lon"]["Angle"]])
        except KeyError:
            print("Error reading BLUE waypoints from JSON")
        self.blue_waypoints = blue_wps

    
    def build_grid(self, print_stats=False):    
        #consider blue waypoints, NAIs, red location, go some factor out from that
        relevant_points = np.array([[self.initial_blue_loc[0],self.initial_blue_loc[1]]] + self.blue_waypoints + self.areas_of_interest)
        grid_center = relevant_points.mean(axis=0)
        self.grid_center = Point(grid_center[0],grid_center[1])

        #extend the grid beyond all relevant points by a factor of num_uxvs*max_comms_range
        grid_factor = (self.num_uavs+self.num_usvs) * units.km(meters=self.max_comms_range)

        #initialize points
        left = right = top = bottom = relevant_points[0]
        #identify leftmost, rightmost, topmost, and bottommost points from those above
        for p in relevant_points:
            if p[1] < left[1]: left = p
            if p[1] > right[1]: right = p
            if p[0] > top[0]: top = p
            if p[0] < bottom[0]: bottom = p
        
        #now identify top_left point (latitude of top, longitude of left)
        top_left = Point(top[0],left[1])
        
        #now compute the grid width and height and extend them by the grid factor
        self.grid_width_km = distance(Point(self.grid_center[0],top_left[1]),self.grid_center).km + grid_factor
        self.grid_height_km = distance(top_left,Point(self.grid_center[0],top_left[1])).km + grid_factor
        grid_corner_distance = math.sqrt(self.grid_width_km**2+self.grid_height_km**2)

        self.grid_top_left = distance(kilometers = grid_corner_distance).destination(point=self.grid_center,bearing=270+math.degrees(math.atan(self.grid_height_km/self.grid_width_km)))
        self.grid_top_right = distance(kilometers = grid_corner_distance).destination(point=self.grid_center,bearing=math.degrees(math.atan(self.grid_width_km/self.grid_height_km)))
        self.grid_bottom_right = distance(kilometers = grid_corner_distance).destination(point=self.grid_center,bearing=180-math.degrees(math.atan(self.grid_width_km/self.grid_height_km)))
        self.grid_bottom_left = distance(kilometers = grid_corner_distance).destination(point=self.grid_center,bearing=180+math.degrees(math.atan(self.grid_width_km/self.grid_height_km)))

        #this is what I did when I wanted to put BLUE FFG at the center and then make a square grid the maximum
        #   distance a UxV could travel in all directions out from that
        #*************************
        """
        self.grid_top_left = distance(kilometers = self.max_distance_from_center * math.sqrt(2)).destination(point=self.initial_blue_loc,bearing=315)
        self.grid_top_right = distance(kilometers = self.max_distance_from_center * math.sqrt(2)).destination(point=self.initial_blue_loc,bearing=45)
        self.grid_bottom_left = distance(kilometers = self.max_distance_from_center * math.sqrt(2)).destination(point=self.initial_blue_loc,bearing=225)
        self.grid_bottom_right = distance(kilometers = self.max_distance_from_center * math.sqrt(2)).destination(point=self.initial_blue_loc,bearing=135)
        """
        #*************************

        #cell_height is the North/South distance of a grid cell
        self.cell_height = distance(self.grid_top_left,self.grid_bottom_left).kilometers/self.grid_height

        #cell_width is the Easy/West distance of a grid cell
        self.cell_width = distance(self.grid_top_left,self.grid_top_right).kilometers/self.grid_width

        water_count = 0
        land_count = 0
        grid = []
        row_top_left = self.grid_top_left
        for i in range(self.grid_height):
            row = []
            cell_top_left = row_top_left
            for j in range(self.grid_width):
                c = Cell(cell_top_left,self.cell_width,self.cell_height,(i,j))
                if(c.type == LandorWater.LAND): land_count += 1
                else: water_count += 1
                row.append(c)
                cell_top_left = distance(kilometers=self.cell_width).destination(point=cell_top_left,bearing=90)
            grid.append(row)
            row_top_left = distance(kilometers=self.cell_height).destination(point=row_top_left,bearing=180)
        self.grid = grid

        if(print_stats):
            print(f"The grid is {self.grid_height} (height) by {self.grid_width} (width)")
            print(f"Each cell is {self.cell_height} km tall and {self.cell_width} km wide")
            print(f"Of the {len(self.grid) * len(self.grid[0])} cells, {land_count} of them are land and {water_count} of them are water.")
            
    def convert_index_to_latlong(self, i: int, j: int) -> Point:
        for row in self.grid:
            for cell in row:
                if(cell.i == i and cell.j == j):
                    return cell.center.format_decimal()
        return Point(latitude=0,longitude=0)

    def convert_latlong_to_index(self, lat: float, lon: float):
        point = ShapelyPoint(lat,lon)
        for row in self.grid:
            for cell in row:
                polygon = Polygon(cell.poly_coords)
                if(polygon.contains(point)):
                    return (cell.i, cell.j)
        return (-1,-1)
    
    def determine_of_interest(self):
        for area in self.areas_of_interest:
            i,j = self.convert_latlong_to_index(area[0],area[1])
            if(i > -1 and j > -1):
                self.grid[i][j].set_of_interest()
    
    def write_grid_to_file(self, file_name):
        with open(file_name, "w") as grid_file:
            grid_file.write(f"{self.grid_height},{self.grid_width}\n")
            grid_file.write(f"{self.num_uavs},{self.num_usvs}\n")
            grid_file.write(f"{self.max_comms_range}\n")
            init_blue_loc = self.convert_latlong_to_index(self.initial_blue_loc.latitude,self.initial_blue_loc.longitude)
            grid_file.write(f"{init_blue_loc[0]},{init_blue_loc[1]}\n")
            red_loc = self.convert_latlong_to_index(self.red_loc.latitude,self.red_loc.longitude)
            grid_file.write(f"{red_loc[0]},{red_loc[1]}\n")
            for wp in self.blue_waypoints[4:]:
                blue_i,blue_j = self.convert_latlong_to_index(wp[0],wp[1])
                grid_file.write(f"{blue_i},{blue_j}")
                if(self.blue_waypoints.index(wp) < len(self.blue_waypoints)-1):grid_file.write(",") 
            grid_file.write("\n")
            grid_file.write("0,0,0,1\n")
            grid_file.write(f"{math.floor(self.max_time/1800)}\n")
            for ai in self.areas_of_interest:
                ai_i,ai_j = self.convert_latlong_to_index(ai[0],ai[1])
                grid_file.write(f"{ai_i},{ai_j}")
                if(self.areas_of_interest.index(ai) < len(self.areas_of_interest)-1):grid_file.write(",") 
            grid_file.write("\n")
            i = 0
            for row in self.grid:
                j = 0
                for cell in row:
                    grid_file.write(f"{i},{j},{cell.type.value},{cell.top_left.latitude},{cell.top_left.longitude},{cell.top_right.latitude},{cell.top_right.longitude},{cell.bottom_right.latitude},{cell.bottom_right.longitude},{cell.bottom_left.latitude},{cell.bottom_left.longitude},{cell.center.latitude},{cell.center.longitude}\n")
                    j += 1
                i += 1