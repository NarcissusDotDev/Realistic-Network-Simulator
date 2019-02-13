from collections import namedtuple
import sys
import gzip
import pyproj

TimePoint = namedtuple("TimePoint", "x y t")

def between(line, start, end, soft=True):
    tmp = ""
    if start in line:
        tmp = line[line.index(start)+len(start):]
        if end in tmp:
            tmp = tmp[:tmp.index(end)]
        elif not soft:
            raise "Not Found"
    elif not soft:
        raise "Not Found"
    
    return tmp

def convert(name, buildings, offset = 0):
    params, c_x, c_y = "", 0, 0
    with open(buildings,'rt') as f:
        text = f.read()
        bounds = between(text,'netOffset="','"').split(",")
        params = between(text,'projParameter="','"')
        c_x, c_y = -float(bounds[0]), -float(bounds[1])

    p = pyproj.Proj(params)
    points = []
    all_points = []
    with gzip.open(name,'rt') as f:
        for line in f:
            row = []
            for point in line.split(", "):
                data = point.replace("[","").replace("]","").replace(","," ").split(" ")
                t, geo_x, geo_y = data[0], data[1], data[2]
                x, y = p(geo_x,geo_y)
                row.append(TimePoint( x-c_x, y-c_y, t ))
                all_points.append(TimePoint( x-c_x, y-c_y, t ))
            points.append(row)

    if offset != 0:
        p = sorted(all_points, key=lambda p: p.x*p.x + p.y*p.y)
        min, max = p[0], p[len(p)-1]
        points[0] = [TimePoint( min.x, min.y, '0.0')]
        points[1] = [TimePoint( max.x, max.y, '0.0')]
        points[2] = [TimePoint( min.x + offset, min.y + offset, '0.0')]
    
    with gzip.open(name.replace(".geo",""),'wt') as out:
        for p in points:
            for time_p in p:
                out.write("%s %s %s " % (time_p.t, time_p.x, time_p.y))
            out.write("\n")
  
if __name__ == "__main__":
    if len(sys.argv) == 3:
        convert(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 4:
        convert(sys.argv[1], sys.argv[2], float(sys.argv[3]))
    else:
        sys.stderr.write('Invalid Number of arguments\n')
        exit(1)

