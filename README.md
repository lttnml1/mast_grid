The format of the grid_output.txt file is:
- height x width
- #ofUAVs, #ofUSVs
- maximum communcations range (in meters)
- a list of blue waypoints i_1,j_1,i_2,j_2,etc.
- destination (a "1" for the side that is destination) [top,right,bottom,left]
- the maximum number of 30-minute cycles that can occur
- the areas of interest i_1,j_1,i_2,j_2,etc.
- for the next 0...NxM rows:
    - i,j,TL_lat,TL_lon,TR_lat,TR_lon,BR_lat,BR_lon,BL_lat,BL_lon,CENTER_lat,CENTER_lon
