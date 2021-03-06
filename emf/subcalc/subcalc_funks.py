from .. import os, np, pd, shutil

from ..emf_funks import (_path_manage, _check_extension, _is_number, _is_int,
                        _check_intable, _flatten, _sig_figs)

import subcalc_class

def drop_footprint_template(*args, **kw):
    """Copy the emf.subcalc footprint template in the current directory or a directory specified by an input string
    args:
        drop_path - string, path of copied template file"""
    #check inputs
    if(len(args) > 1):
        raise(fields_class.EMFError("""drop_footprint_template only accepts zero or one input argument. A string can be passed to specify the directory in which the template file is copied. With no arguments, the template file is copied into the current directory."""))
    elif(len(args) == 1):
        kw = {'path': args[0]}
    #get template file path
    fn_temp = os.path.dirname(os.path.dirname(__file__))
    fn_temp = os.path.join(fn_temp, 'templates')
    fn_temp = os.path.join(fn_temp, 'subcalc-footprint-template.xlsx')
    #get drop path
    fn_drop = _path_manage('subcalc-footprint-template', 'xlsx', **kw)
    #check for existing files
    if(os.path.isfile(fn_drop)):
        raise(subcalc_class.EMFError('A file with the path "%s" already exists. Move/delete it or pass a new path string to drop_footprint_template().' % fn_drop))
    #copy and notify
    shutil.copyfile(fn_temp, fn_drop)
    print('emf.fields template written to: %s' % fn_drop)

def load_results(*args, **kw):
    """Read a .REF output file and load the data into a Results object
    args:
        results_path - string, path to the output .REF file of field results or to
                the excel file exported by a Results object
        footprint_path - string, optional, path to the csv file of
                         footprint data
    kw:
        Bkey - string, sets 'component' of magnetic field results that the
               returned Results object accesses by default
                     - can be 'Bx', 'By', 'Bz', 'Bmax', or 'Bres'
                     - default is 'Bmax'
                     - all components are stored, none are lost
    returns
        res - Results object containing results"""

    #check for a Bkey kwarg
    if('Bkey' in kw):
        Bkey = kw['Bkey']
    else:
        Bkey = 'Bmax'

    #check extensions
    try:
        fn = _check_extension(args[0], '.REF', '')
    except(subcalc_class.EMFError):
        fn = _check_extension(args[0], '.xlsx', """
        Can only load Results from .REF or .xlsx files""")


    if(fn[-3:] == 'REF'):

        #pull data from the REF file
        data, info = read_REF(args[0])
        #get the gridded arrays
        data = meshgrid(data)
        #initialize Results object
        res = subcalc_class.Results(data, info, Bkey=Bkey)
        #check for footprint file path and load if present
        if(len(args) > 1):
            res.load_footprints(args[1])

    elif(fn[-4:] == 'xlsx'):
        #get a dict of all sheets in excel file
        dfs = pd.read_excel(args[0], sheetname=None)
        bkeys = dfs.keys()
        if('info' in bkeys):
            bkeys.remove('info')
        if('footprints' in bkeys):
            bkeys.remove('footprints')
        #slice out grid data
        x = [float(i) for i in dfs[bkeys[0]].columns]
        y = [float(i) for i in dfs[bkeys[0]].index]
        X, Y = np.meshgrid(x, y)
        data = {'X': X, 'Y': Y}
        for k in bkeys:
            data[str(k)] = dfs[k].values
        #slice out info dictionary
        if('info' in dfs):
            info = dfs['info']
            params = info[info.columns[0]].values
            values = info[info.columns[1]].values
            info = dict(zip(params, values))
            #initialize Results with metadata
            res = subcalc_class.Results(data, info, Bkey=Bkey)
        #initialize Results object without metadata dict
        res = subcalc_class.Results(data, Bkey=Bkey)

        #check for footprints
        if(len(args) > 1):
            #check for footprint file path and load if present
            res.load_footprints(args[1])
        elif('footprints' in dfs):
            res.load_footprints(dfs['footprints'])

    else:
        raise(subcalc_class.EMFError("""
        Results must be loaded from .REF file or excel files"""))

    #return
    return(res)

def convert_REF(*args, **kw):
    """Convert a .REF results file to an excel file storing the same data and save the excel file
    args:
        REF_path - string, path to the .REF file
        footprint_path - string, optional, path to footprint csv file
    kw:
        path - string, path/name of output file"""

    #load and export the results
    load_results(*args, **kw).export(**kw)

def read_REF(file_path):
    """Reads a .REF output file generated by the SUBCALC program, pulling out x and y coordinates for the results and all the magnetic field "components"
    args:
        file_path - string, path to saved .REF output file
    returns:
        data - dict, keys are 'x', 'y', 'Bmax', 'Bres', 'Bx', 'By', and 'Bz'
        info - dict, reference grid and other information"""

    #check the extension
    file_path = _check_extension(file_path, 'REF', """
        SubCalc results are saved to text files with .REF extensions.
        The input path:
            "%s"
        does not have the correct extension.""" % file_path)

    #allocate dictionaries
    info = {'REF_path': file_path} #dictionary storing reference grid information
    keys = ['X Coord', 'Y Coord', 'X Mag', 'Y Mag', 'Z Mag', 'Max', 'Res']
    return_keys = ['x', 'y', 'bx', 'by', 'bz', 'bmax', 'bres']
    data = dict(zip(keys, [[] for i in range(len(keys))]))

    #pull data out
    with open(file_path, 'r') as ifile:
        #store information about the grid
        for i in range(24):
            line = ifile.readline().strip()
            if(':' in line):
                idx = line.find(':')
                line = [line[:idx], line[idx+1:]]
                if(_is_number(line[1])):
                    info[line[0]] = float(line[1])
                else:
                    info[line[0]] = line[1].strip()
        #read through the rest of the data
        for line in ifile:
            for k in keys:
                if(k == line[:len(k)]):
                    L = line[8:].rstrip()
                    data[k].append([float(L[i:i+8]) for i in range(0, len(L)-1, 8)])

    #flatten the lists in data
    for k in data:
        data[k] = np.array(_flatten(data[k]))

    #switch the keys
    data = dict(zip(return_keys, [data[k] for k in keys]))

    return(data, info)

def meshgrid(flat_data):
    """Convert raw grid data read from a SubCalc output file (by subcalc_funks.read_REF) into meshed grids of X, Y coordinates and their corresponding B field values
    args:
        flat_data - dict, keyed by 'x','y','bx','by','bz','bmax','bres'
    returns:
        grid_data - dict with 2D arrays keyed by
                'X','Y','Bx','By','Bz','Bmax','Bres'"""

    #find the number of points in a row
    x = flat_data['x']
    y = flat_data['y']
    count = 0
    v = y[0]
    while(y[count] == v):
        count += 1
    #get ncols and nrows
    L = len(x)
    ncols = count
    nrows = L/ncols
    #map old to new keys
    mapk = dict(zip(['x','y','bx','by','bz','bmax','bres'],
                    ['X','Y','Bx','By','Bz','Bmax','Bres']))
    #replace with 2D arrays
    grid_data = dict(zip([mapk[k] for k in flat_data],
                [np.reshape(flat_data[k], (nrows, ncols)) for k in flat_data]))

    return(grid_data)

def _bilinear_interp(res, x, y):
    """Use Results to interpolate linearly in two dimensions for an estimate of any x,y coordinate inside the grid.
    args:
        res - Results object
        x - float, x coordinate to interpolate at
        y - float, y coordinate to interpolate at
    returns:
        B_interp - float, interpolated field value"""
    #first find the 4 point grid cell containing x,y
    #   (the point is assumed to lie inside the grid)
    _, xidx = _double_min(np.abs(res.x - x))
    _, yidx = _double_min(np.abs(res.y - y))
    #get coordinates and values
    x1, x2 = res.x[xidx]
    y1, y2 = res.y[yidx]
    B11 = res.B[yidx[0], xidx[0]]
    B12 = res.B[yidx[0], xidx[1]]
    B21 = res.B[yidx[1], xidx[0]]
    B22 = res.B[yidx[1], xidx[1]]
    #interpolate
    ym1 = y - y1
    xm1 = x - x1
    y2m = y2 - y
    x2m = x2 - x
    B_interp = ((1.0/((x2 - x1)*(y2 - y1)))
                *(x2m*(B11*y2m + B12*ym1) + xm1*(B21*y2m + B22*ym1)))

    return(B_interp)

def _2Dmax(G):
    """Find the indices and value of the maximum value in a 2 dimensional array
    args:
        G - 2D numpy array
    returns:
        m - the maximum value
        i - index of max along 0th axis
        j - index of max along 1st axis"""
    imax, jmax = 0, 0
    m = np.min(G)
    for i in range(G.shape[0]):
        for j in range(G.shape[1]):
            if(G[i,j] > m):
                m = G[i,j]
                imax = i
                jmax = j
    return(m, imax, jmax)

def _2Dmin(G):
    """Find the indices and value of the minimum value in a 2 dimensional array
    args:
        G - 2D numpy array
    returns:
        m - the minimum value
        i - index of max along 0th axis
        j - index of max along 1st axis"""
    imin, jmin = 0, 0
    m = np.max(G)
    for i in range(G.shape[0]):
        for j in range(G.shape[1]):
            if(G[i,j] < m):
                m = G[i,j]
                imin = i
                jmin = j
    return(m, imin, jmin)

def _double_min(v):
    """Find the lowest two values in an array and their indices
    args:
        v - iterable
    returns:
        mins - array of minima, the first one being the smallest
        idxs - array of indices of minima"""
    if(len(v) < 2):
        raise(subcalc_class.EMFError("""
        Cannot find lowest two values in an array of length less than 2."""))
    m = max(v) #store the max for initialization
    mins = np.array([m, m], dtype=float)
    idxs = np.zeros((2,), dtype=int)
    for i in range(len(v)):
        if(v[i] < mins[0]):
            #swap first minimum to second
            mins[1] = mins[0]
            idxs[1] = idxs[0]
            #store new first minimum
            mins[0] = v[i]
            idxs[0] = i
        elif(v[i] < mins[1]):
            #store new second minimum
            mins[1] = v[i]
            idxs[1] = i

    return(mins, idxs)

_dist = lambda x1, x2, y1, y2: np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def cumulative_distance(*args):
    """calculate the cumlative linear distances along a path of x,y coordinates, including the first point (the returned array always starts with zero)
    args:
        either a single iterable of x,y pairs or two iterables representing
        x and y coordinates seperately
    returns:
        dist - array, cumulative distance along the points"""

    if(len(args) == 1):
        p = args[0]
        d = np.zeros((len(p),), dtype=float)
        for i in range(1, len(args[0])):
            d[i] = _dist(p[i][0], p[i-1][0], p[i][1], p[i-1][1]) + d[i-1]
    elif(len(args) == 2):
        x, y = args[0], args[1]
        d = np.zeros((len(x),), dtype=float)
        for i in range(1, len(x)):
            d[i] = _dist(x[i], x[i-1], y[i], y[i-1]) + d[i-1]
    else:
        raise(emf_class.EMFError('cumulative_distance only accepts 1 or 2 arguments.'))

    return(d)
