from .. import np, pd, os, copy, _interpn

from ..emf_class import EMFError

import subcalc_funks

class Model(object):
    """Model objects store Tower and/or Conductor objects, information about the desired model grid, and provide the means of computing model results and returning them in a Results object."""
    pass

class Tower(object):
    """Tower objects are used to define the locations of power lines in a Model.

    Towers are connected by their 'group' strings. Towers with the same 'group' are assumed to carry the same wires through a model domain. Thus, because Tower objects in the same group are carrying the same conductors, the order of their 'h', 'v', 'I', and 'phase' properties matters. For example, for a single Tower, all of the 0th elements of those properties correspond to a the same individual wire. For the path of that wire to be accurately calculated, it must also be in the 0th position in Towers of the same group. Towers in the same group must also have the same number of wires, meaning their 'h', 'v', 'I', and 'phase' arrays must have the same lengths.

    The sequence of Towers in a group is defined by thier 'seq' property. Current is assumed to flow from the Tower with Tower with the lowest 'seq' value to the Tower with the next lowest 'seq' value, and so on."""

    def __init__(self, num, x, y, rot, h, v, I, phase, group):
        """
        args:
            group - str, a string used to group towers together into continuous
                    circuits
            seq - int, a number describing the position of this tower among
                  other towers in the same group, where current is assumed to
                  run from the 0th tower to the 1st, 2nd, ...
            tower_x - the x coordinate of the tower/pole in the model grid (ft)
            tower_y - the y coordinate of the tower/pole in the model grid (ft)
            tower_rot - the rotation angle of the tower in degrees, where
                        zero degrees points along the positive x axis and the
                        rotation increases clockwise
            h - iterable of numbers, the horizontal locations of conductors
                on the tower (ft)
            v - iterable of numbers, the vertical locations of conductors
                on the tower (ft)
            I - iterable of numbers, the current amplitudes of conductors
                on the tower (Amps)
            phase - iterable of numbers, the phase angles of conductors on the
                    tower (degrees)"""

        self._group = None
        self._seq = None
        self._x = None
        self._y = None
        self._rot = None
        self._h = None
        self._v = None
        self._I = None
        self._phase = None

        self.group = group
        self.seq = seq
        self.x = x
        self.y = y
        self.rot = rot
        self.h = h
        self.v = v
        self.I = I
        self.phase = phase

    #-----------------------------------------------------------------------
    #properties

    def _get_group(self): return(self._group)
    def _set_group(self, value): self._group = str(value)
    group = property(_get_group, _set_group, None, 'String used to group towers together into continuous circuits. All Towers in the same circuit have the same group string.')

    def _get_seq(self): return(self._seq)
    def _set_seq(self, value): self._seq = int(value)
    seq = property(_get_seq, _set_seq, None, 'Integer describing the position of this tower among other towers in the same group, where current is assumed to run from the 0th tower to the 1st, 2nd, ...')

    def _get_x(self): return(self._x)
    def _set_x(self, value): self._x = float(value)
    x = property(_get_x, _set_x, None, 'Tower x coordinate within the model domain (ft)')

    def _get_y(self): return(self._y)
    def _set_y(self, value): self._y = float(value)
    y = property(_get_y, _set_y, None, 'Tower y coordinate within the model domain (ft)')

    def _get_conductor_x(self): return(self.x + np.cos(self.rot_rad)*self.h)
    conductor_x = property(_get_conductor_x, None, None, 'x-axis coordinates of the conductors on the tower in the model domain, calculated from Tower.x, Tower.h, and Tower.rot')

    def _get_conductor_y(self): return(self.y + np.sin(self.rot_rad)*self.h)
    conductor_y = property(_get_conductor_y, None, None, 'y-axis coordinates of the conductors on the tower in the model domain, calculated from Tower.y, Tower.h, and Tower.rot')

    def _get_conductor_z(self): return(self.h)
    conductor_z = property(_get_conductor_z, None, None, 'z-axis coordinates of the conductors on the tower in the model domain, identical to Tower.h')

    def _get_rot(self): return(self._rot)
    def _set_rot(self, value): self._rot = float(value)
    rot = property(_get_rot, _set_rot, None, 'Tower rotation (degrees), where zero degrees points along the positive x axis and the rotation increases clockwise')

    def _get_rot_rad(self): return((self._rot/360.0)*2*np.pi)
    def _set_rot_rad(self, value): self._rot = (float(value)/(2*np.pi))*360.0
    rot_rad = property(_get_rot_rad, _set_rot_rad, None, 'Tower rotation (radians), where zero degrees points along the positive x axis and the rotation increases clockwise')

    def _get_h(self): return(self._h)
    def _set_h(self, value): self._h = np.array(value, dtype=float)
    h = property(_get_h, _set_h, None, 'Horizontal locations of conductors on the tower (ft)')

    def _get_v(self): return(self._v)
    def _set_v(self, value): self._v = np.array(value, dtype=float)
    v = property(_get_v, _set_v, None, 'Vertical locations of conductors on the tower (ft)')

    def _get_I(self): return(self._I)
    def _set_I(self, value): self._I = np.array(value, dtype=float)
    I = property(_get_h, _set_h, None, 'Current amplitudes of conductors on the tower (Amps)')

    def _get_phase(self): return(self._phase)
    def _set_phase(self, value): self._phase = np.array(value, dtype=float)
    phase = property(_get_phase, _set_phase, None, 'Phase angles of conductors on the tower (degrees)')


class Conductor(object):
    """Conductor objects represent single wires running through a Model domain. They can be used to specify the coordinates of conductor paths directly, instead of through the properties of a Tower object. Tower and Conductor objects together are the means of creating wires in a model domain."""

    def __init__(self, x, y, z, I, phase):
        """
        args:
            x - iterable of at least two numbers, the x coordinates of the
                Conductor path in the model domain (ft)
            y - iterable of at least two numbers, the y coordinates of the
                Conductor path in the model domain (ft)
            z - iterable of at least two numbers, the z coordinates of the
                Conductor path in the model domain (ft)
            I - float, amplitude of the current in the Conductor, assumed to
                flow from (x[0], y[0], z[0]) to (x[-1], y[-1], z[-1]) (Amps)
            phase - float, the phase angle of the current flow (degrees)"""

        self._x = None
        self._y = None
        self._z = None
        self._I = None
        self._phase = None

        self.x = x
        self.y = y
        self.z = z
        self.I = I
        self.phase = phase

    #---------------------------------------------------------------------------
    #properties

    def _get_x(self): return(self._x)
    def _set_x(self, value):
        if(not hasattr(value, len)):
            raise(EMFError('The x property of a Conductor must be a iterable of at least two numbers.'))
        elif(len(value) < 2):
            raise(EMFError('The x property of a Conductor must have at least two numeric elements.'))
        self._x = np.array(value, dtype=float)
    x = property(_get_x, _set_x, None, 'x coordinates of the Conductor path in the model domain (ft)')

    def _get_y(self): return(self._y)
    def _set_y(self, value):
        if(not hasattr(value, len)):
            raise(EMFError('The y property of a Conductor must be a iterable of at least two numbers.'))
        elif(len(value) < 2):
            raise(EMFError('The y property of a Conductor must have at least two numeric elements.'))
        self._y = np.array(value, dtype=float)
    y = property(_get_y, _set_y, None, 'y coordinates of the Conductor path in the model domain (ft)')

    def _get_z(self): return(self._z)
    def _set_z(self, value):
        if(not hasattr(value, len)):
            raise(EMFError('The z property of a Conductor must be a iterable of at least two numbers.'))
        elif(len(value) < 2):
            raise(EMFError('The z property of a Conductor must have at least two numeric elements.'))
        self._z = np.array(value, dtype=float)
    z = property(_get_z, _set_z, None, 'z coordinates of the Conductor path in the model domain (ft)')

    def _get_I(self): return(self._I)
    def _set_I(self, value):
        if(not subcalc_funks._is_number(value)):
            raise(EMFError('The I property of Conductor objects must be a number defining the amplitude of the current in the Conductor (Amps).'))
        self._I = float(value)
    I = property(_get_I, _set_I, None, 'amplitude of the current in the Conductor, assumed to flow from (x[0], y[0], z[0]) to (x[-1], y[-1], z[-1]) (Amps)')

    def _get_phase(self): return(self._phase)
    def _set_phase(self, value):
        if(not subcalc_funks._is_number(value)):
            raise(EMFError('The phase property of Conductor objects must be a number defining the phase angle of the current (degrees).'))
        self._phase = float(value)
    phase = property(_get_phase, _set_phase, None, 'the phase angle of the current flow (degrees)')

class Results(object):
    """Results objects store the results of magnetic field modeling generated by the SubCalc program. A Results can be created by passing grid results directly or by passing a dictionary of grid results. The function subcalc.load_results is the best way to generate a Results object from a .REF file containing SubCalc results. The Results object can be saved to a more flexible (and smaller) excel file with Results.export(). Then the excel file can be read back into a Results object using subcalc.load_results.

    Results objects have a 'Bkey' property that determines which component of the magnetic field results is accessed by the Results.B property. For example, when Results.Bkey == 'Bmax' all operations involving the grid of magnetic field results accessed by Results.B will operate on the 'max' field component. When Bmax == 'Bz' all operations deal with the vertical 'z' component of the field, and so on. This includes plotting.

    Footprints of objects in the Results domain like buildings, the power lines, fences, etc. can also be stored in Results objects. Data for these objects can be saved in csv template files. The path of the footprint csv files can be passed to subcalc.load_results for automatic inclusion in a newly generated Results object or it can be passed to an existing Results with Results.load_footprints. The footprint data is stored in Footprint objects that have very little functionality and are mostly just organizational objects.

    Several methods are available for interpolating new values from the grid of field results: Results.interp, Results.segment, Results.path, and Results.resample.

    There are also methods for selecting a subset of a Results object's domain and for shifting its x,y coordinates. These are Results.zoom and Results.rereference respectively.

    Contour plots of the results (Results.B) can be automatically generated with subcalc.plot_contour(Results) and colormesh plots can be automatically generated with subcalc.plot_pcolormesh(Results). The fields along a path through the Results domain (essentially a cross section) can be plotted with subcalc.plot_path. A contour or pcolormesh can be combined with cross sections using the subcalc.plot_cross_sections function."""

    def __init__(self, *args, **kw):
        """Grid data must be passed in
        args:
            either:
                X - 2D array of x coordinates
                Y - 2D array of y coordinats
                B - 2D array of magnetic field magnitudes
                info - dict, optional, dictionary of results metadata
            or:
                data - dict, dictionary with X, Y, and B grids, should be
                            keyed by 'X','Y','Bmax','Bres','Bx','By','Bz'
                info - dict, optional, dictionary of results metadata
        kw:
            Bkey - str, selects which component of field results to use
                    or defines which component is passed as grid arrays
                    ('Bmax', 'Bres', 'Bx', 'By', 'Bz')."""

        largs = len(args)

        self._name = None

        #inputs must correspond to the second case, dictionary of data and
        #optional dict of metadata
        if(largs <= 2):
            #check args[0]
            if(type(args[0]) is not dict):
                raise(EMFError("""The first argument to Results() must be a dictionary of result information when passing 1 or 2 arguments to initialize the Results, not %s""" % type(args[0])))
            #check keys
            s = set(['X','Y','Bmax','Bres','Bx','By','Bz'])
            k = set(args[0].keys())
            if(any([(i not in s) for i in k])):
                raise(EMFError("""If passing a dictionary to initialize a Results object, the dict can have the following keys only:
                    %s""" % str(s)))
            if(('X' not in k) or ('Y' not in k)):
                raise(EMFError("""If passing a dictionary to initialize a Results object, the dictionary must have 'X' and 'Y' keys, which lead to grid coordinate arrays."""))
            if(len(k) < 3):
                raise(EMFError("""If passing a dictionary to initialize a Results object, the dictionary must be keyed by 'X', 'Y', and any number of the following keys:
                    %s""" % str(['Bmax','Bres','Bx','By','Bz'])))
            #store data
            self._grid = args[0]
            #deal with Bkey
            if('Bkey' in kw):
                self.Bkey = kw['Bkey']
            elif('Bmax' in k):
                self.Bkey = 'Bmax'
            else:
                self.Bkey = list(k)[0]
            #store the info dict if present
            if(largs == 2):
                if(type(args[1]) is not dict):
                    raise(EMFError("""The fourth argument to Results() must be a dictionary of  results information, not %s""" % type(args[1])))
                self._info = args[1]
            else:
                self._info = None

        #inputs must correspond to the first case, grids passed in directly
        elif(largs <= 4):
            #check input types
            msg = """If passing three or four arguments to initialize a Results, the first three arguments must be 2D numpy arrays representing X, Y, and B grids respectively, each with the same shape."""
            for i in range(3):
                if(type(args[i]) is not np.ndarray):
                    raise(EMFError(msg))
                elif(len(args[i].shape) != 2):
                    raise(EMFError(msg))
                elif(args[i].shape != args[1].shape):
                    raise(EMFError(msg))
            #2D reference grid arrays
            if('Bkey' in kw):
                self._Bkey = kw['Bkey']
            else:
                self._Bkey = 'unknown'
            self._grid = {'X': args[0], 'Y': args[1], self._Bkey: args[2]}
            #store the info dict if present
            if(largs == 4):
                if(type(args[3]) is not dict):
                    raise(EMFError("""The fourth argument to Results() must be a dictionary of results information, not type %s""" % type(args[3])))
                self._info = args[3]
            else:
                self._info = None

        #other reference objects in the results domain, like substatio
        #boundaries, stored in a list of Footprint objects
        self.footprint_df = None #DataFrame of Footprint information
        self._footprints = []
        #angle of the northern direction with respect to the grid
        #   where 0 degrees is the positive y axis and clockwise is increasing
        self._north_angle = None

    #---------------------------------------------------------------------------
    #properties

    def _get_name(self):
        if(self._name is None):
            return('unnamed-results')
        else:
            return(self._name)
    def _set_name(self, value):
        if(not value):
            raise(EMFError('Results.name should be a string.'))
        self._name = str(value)
    name = property(_get_name, _set_name, None, 'Name of results object, used for filenames when exporting')

    def _get_B(self):
        return(self._grid[self._Bkey])
    B = property(_get_B, None, None, '2D grid of magnetic field results with y-coordinates decreasing down the rows and x-coordinates inreasing along the columns. For example, B[0,0] retrieves the result at the lowest x value and highest y value and B[-1,-1] retrieves the result at the higest x value and lowest y value. The grid is arranged so that the coordinate arrays print in the same way they are arranged on a cartesian plane.')

    def _get_Bkeys(self):
        k = self._grid.keys()
        k.remove('X')
        k.remove('Y')
        return(set(k))
    Bkeys = property(_get_Bkeys, None, None, 'A set of available Bkey values in the Results')

    def _get_Bkey(self):
        return(self._Bkey)
    def _set_Bkey(self, value):
        if(value not in self.Bkeys):
            raise(EMFError('Bkey must be set to one of the following elements:\n%s' % str(self.Bkeys)))
        else:
            self._Bkey = value
    Bkey = property(_get_Bkey, _set_Bkey, None, 'Component of magnetic field accessed by the B property')

    def _get_info(self): return(self._info)
    info = property(_get_info, None, None, 'Dictionary of results metadata')

    def _get_footprints(self): return(self._footprints)
    footprints = property(_get_footprints, None, None, 'List of Footprint objects')

    def _get_X(self):
        return(self._grid['X'])
    X = property(_get_X, None, None, '2D grid of reference grid x coordinates')

    def _get_Y(self):
        return(self._grid['Y'])
    Y = property(_get_Y, None, None, '2D grid of reference grid y coordinates')

    def _get_x(self):
        return(self.X[0,:])
    x = property(_get_x, None, None, 'Unique x values in results grid (column positions)')

    def _get_y(self):
        return(self.Y[:,0])
    y = property(_get_y, None, None, 'Unique y values in results grid (row positions)')

    def _get_xmax(self):
        return(np.max(self.x))
    xmax = property(_get_xmax, None, None, 'Maximum horizontal coordinate in results')

    def _get_xmin(self):
        return(np.min(self.x))
    xmin = property(_get_xmin, None, None, 'Minimum horizontal coordinate in results')

    def _get_ymax(self):
        return(np.max(self.y))
    ymax = property(_get_ymax, None, None, 'Maximum vertical coordinate in results')

    def _get_ymin(self):
        return(np.min(self.y))
    ymin = property(_get_ymin, None, None, 'Minimum vertical coordinate in results')

    def _get_Bmax(self): return(subcalc_funks._2Dmax(self.B)[0])
    Bmax = property(_get_Bmax, None, None, 'Maximum value of Results.B')

    def _get_loc_Bmax(self):
        m,i,j = subcalc_funks._2Dmax(self.B)
        return(self.x[j], self.y[j])
    loc_Bmax = property(_get_loc_Bmax, None, None, 'x,y coordinates of maximum of Results.B')

    def _get_idx_Bmax(self):
        m,i,j = subcalc_funks._2Dmax(self.B)
        return(i, j)
    idx_Bmax = property(_get_idx_Bmax, None, None, 'indices of maximum of Results.B, along the 0th axis then the 1st axis')

    def _get_Bmin(self): return(subcalc_funks._2Dmin(self.B)[0])
    Bmin = property(_get_Bmin, None, None, 'Minimum value of Results.B')

    def _get_north_angle(self):
        return(self._north_angle)
    def _set_north_angle(self, angle):
        if(not subcalc_funks._is_number(angle)):
            raise(EMFError("""The 'north_angle' attribute of a Results object must be a number."""))
        else:
            self._north_angle = float(angle)
    north_angle = property(_get_north_angle, _set_north_angle, None, """Angle of the Northern direction in degrees, where 0 represents the vertical or Y direction and clockwise represents increasing angle""")

    def _get_footprint_groups(self):
        """Generate a list of lists of Footprints with identical tags"""
        u = list(set([f.group for f in self.footprints]))
        groups = [[] for i in range(len(u))]
        for i in range(len(self.footprints)):
            fp = self.footprints[i]
            groups[u.index(fp.group)].append(fp)
        return(groups)
    footprint_groups = property(_get_footprint_groups)

    #---------------------------------------------------------------------------
    #methods

    def __str__(self):
        return(
        'Results object\n    name: %s\n    components/Bkeys: %s\n    B field range (%s): %g to %g mG\n    x limits: [%g, %g] ft\n    y limits: [%g, %g] ft\n    total samples: %d' %
        (repr(self.name), str(self.Bkeys), self.Bkey, self.Bmin, self.Bmax, self.xmin, self.xmax, self.ymin, self.ymax, len(self.x)*len(self.y))
        )

    def load_footprints(self, footprint_info, **kw):
        """Read footprint data from a csv file and organize it in Footprint objects stored in self.footprints
        args:
            footprint_info - string, path to the footprint csv/excel data.
                            If footprint data is in an excel workbook with,
                            multiple sheets, the sheet name must be passed
                            to the kwarg 'sheet'

                                or

                            an existing DataFrame with footprint data"""
        #load file if footprint_info is not a DataFrame
        if(not (type(footprint_info) is pd.DataFrame)):
            #check extension
            footprint_info = subcalc_funks._check_extension(footprint_info,
                'csv', 'Footprint files must be csv files.')
            #load data
            df = pd.read_csv(footprint_info)
        else:
            df = footprint_info
        #store the DataFrame
        self.footprint_df = df
        #check all columns are present
        cols = ['Group', 'Name', 'X', 'Y', 'Power Line?', 'Of Concern?',
                'Draw as Loop?', 'Group']
        if(set(cols) - set(df.columns)):
            raise(EMFError("""
            Footprint csv files must have the following column names:
            %s
            The footprint csv file with path:
            %s
            is missing or misspells these columns:
            %s""" % (str(cols), footprint_info,
                    str(list(set(cols) - set(df.columns))))))
        message = """
            The column:
                "%s"
            must contain only one repeated value for each footprint.
            It contained multiple values for footprint name:
                "%s" """
        #pick out some columns
        fields = cols[4:]
        #clear the footprints list
        self._footprints = []
        #create a footprint for unique entries in the 'Name' field
        for n in df['Name'].unique():
            s = df[df['Name'] == n]
            #check that certain fields only contain a single entry
            for f in fields:
                if(len(s[f].unique()) > 1):
                    raise(EMFError(message % (f,n)))
            fp = Footprint(n, s['X'].values, s['Y'].values,
                    bool(s['Power Line?'].unique()[0]),
                    bool(s['Of Concern?'].unique()[0]),
                    bool(s['Draw as Loop?'].unique()[0]),
                    s['Group'].unique()[0])
            self.footprints.append(fp)

    def path(self, points, n=101, close_path=False):
        """Interpolate the field along a path defined by lists of x and y
        coordinates
        args:
            points - an iterable of x,y pairs representing a path through the
                     results grid, for example: [(1,2), (1,3), (2,4)]
        optional args:
            n - integer, approximate total number of points sampled. Each
                segment will have at least two samples (the beginning and end
                of the segment). The default is 101.
            close_path - bool, if True, append a segment to the end of the
                         path connecting the first and last points
        returns:
            x - array of x coordinates sampled along the path, will
                include all input coordinates
            y - array of y coordinates sampled along the path, will
                include all input coordinates
            B_interp - interpolated values corresponding to the input
                       coordinates"""
        #check closing path kw
        if(close_path):
            points = list(points)
            points.append(points[-1])
        L = len(points) - 1
        rL = range(L)
        #distribute point count for multiple segements, or don't
        if(L > 1):
            #get x and y
            x, y = zip(*points)
            #calculate distances of each segment
            d = np.array([np.sqrt((x[i]-x[i+1])**2+(y[i]-y[i+1])**2) for i in rL])
            #convert distances to fractions
            d = d/sum(d)
            #approximately distribute the total number of points to each segment
            n = np.ceil(n*d)
            #make sure there are at least two samples in each segment
            n[n < 2] = 2
        else:
            n = [n]
        #interpolate over each segment
        segs = [self.segment(points[i], points[i+1], n[i]) for i in rL]
        x, y, B_interp = (subcalc_funks._flatten(i) for i in zip(*segs))

        return(np.array(x), np.array(y), np.array(B_interp))

    def segment(self, p1, p2, n=101):
        """Interpolate the field along a line between two points
        args:
            p1 - iterable, an x-y pair
            p2 - iterable, an x-y pair
        optional args:
            n - integer, number of points sampled (default 101)
        returns:
            x - array, x coordinates of interpolated values
            y - array, y coordinates of interpolated values
            B_interp - array, interpolated field values"""
        #check point lengths
        if((len(p1) != 2) or (len(p2) != 2)):
            raise(EMFError('Points must consist of two values (xy pairs).'))
        #create x and y vectors
        x, y = np.linspace(p1[0], p2[0], n), np.linspace(p1[1], p2[1], n)
        B_interp = self.interp(x, y)
        return(x, y, B_interp)

    def interp(self, x, y):
        """Interpolate in the x and y directions to find an estimated B value at an x,y location within the results grid
        args:
            x - iterable or scalar, x coordinate(s) to interpolate at
            y - iterable or scalar, y coordinate(s) to interpolate at
        returns:
            B_interp - array or float, the interpolated field value"""
        #make x,y iterable if scalars are passed in
        if(not (hasattr(x, '__len__') and hasattr(y, '__len__'))):
            scalar = True
            x = np.array([x], dtype=float)
            y = np.array([y], dtype=float)
        else:
            scalar = False
        #check that all points are in the grid
        if(not all([self.in_grid(x[i],y[i]) for i in range(len(x))])):
            raise(EMFError("""
            x,y coordinates must fall inside the reference grid:
                range of x coordinates: %g to %g
                range of y coordinates: %g to %g""" %
                (self.xmin, self.xmax, self.ymin, self.ymax)))
        #interpolate
        B_interp = np.array([subcalc_funks._bilinear_interp(self, x[i], y[i])
                                for i in range(len(x))])
        #return
        if(scalar):
            return(B_interp[0])
        else:
            return(B_interp)

    def in_grid(self, x, y):
        """Check if an x,y coordinate pair is inside the Results grid
        args:
            x - float, x coordinate
            y - float, y coordinate
        returns:
            b - bool, True if x,y is in the grid, False if it's not"""
        if((x > self.xmax) or
            (x < self.xmin) or
                (y > self.ymax) or
                    (y < self.ymin)):
            return(False)
        else:
            return(True)

    def resample(self, **kw):
        """Resample the results grid along a new number of x,y values, a new selection of x,y values, or a new number of total values
        kw:
            x - int or iterable, new number of x samples or new selection of
                x samples
            y - int or iterable, new number of y samples or new selection of
                y samples
            N - int, new approximate number of total samples
                    - overrides x and y kw
                    - preserves approx ratio of number of x and y values
                    - rounds up to nearest possible whole number of points
        returns:
            res_resample - a new Results object containing the resampled grid"""

        #check inputs
        if(not kw):
            raise(EMFError('Keyword arguments are required by Results.resample'))
        #store grid x,y extents
        xmin, xmax = self.xmin, self.xmax
        ymin, ymax = self.ymin, self.ymax
        #get 1D vectors of x and y coordinates to resample at, from kw
        if('N' in kw):
            N = kw['N']
            if(not subcalc_funks._is_int(N)):
                raise(EMFError('Keyword argument "N" must be a whole number'))
            N = float(N)
            aspect = float(self.B.shape[0])/self.B.shape[1]
            N_y = np.ceil(np.sqrt(N/aspect))
            N_x = np.ceil(N/N_y)
            x = np.linspace(xmin, xmax, N_x)
            y = np.linspace(ymin, ymax, N_y)
        else:
            if('x' in kw):
                x = kw['x']
                if(subcalc_funks._is_int(x)):
                    x = np.linspace(xmin, xmax, x)
            else:
                x = self.x
            if('y' in kw):
                y = kw['y']
                if(subcalc_funks._is_int(y)):
                    y = np.linspace(ymin, ymax, y)
            else:
                y = self.y
        #flip y coordinates so that Y prints intuitively
        y = y[::-1]
        #resample the grid
        X, Y = np.meshgrid(x, y)
        #some arrays have to be flipped to conform to conventions of _interpn
        B_resample = _interpn((self.y[::-1], self.x),
                                self.B[::-1,:],
                                (Y[::-1,:], X))

        #return with re-flipped results
        res_resample = Results(X, Y, B_resample[::-1,:],
                copy.deepcopy(self.info),
                Bkey=self.Bkey)
        res_resample.load_footprints(self.footprint_df)
        return(res_resample)

    def rereference(self, x_ref=0, y_ref=0, inplace=False):
        """Redefine the coordinates of the bottom left corner of the results grid (the lowest values along each axis) and increment values in the spatial grids accordingly. If no value is provided, spatial grids are adjusted start at (0, 0).
        optional args:
            x_ref - float, new starting value for the x axis, default is zero
            y_ref - float, new starting value for the y axis, default is zero
            inplace - bool, if True, the Results is rereferenced in place,
                      otherwise a rereferenced copy is returned."""
        #get variables
        if(inplace):
            res = self
        else:
            res = self.copy()
        X, Y = res.X, res.Y
        #rereference the grid and child footprint objects
        xdif, ydif = np.min(X) - x_ref, np.min(Y) - y_ref
        X -= xdif
        Y -= ydif
        for i in range(len(res.footprints)):
            x, y = res._footprints[i]._x, res._footprints[i]._y
            res._footprints[i]._x = [j - xdif for j in x]
            res._footprints[i]._y = [j - ydif for j in y]
        if(not inplace):
            return(res)

    def zoom(self, x_range, y_range, inplace=False, rereference=False):
        """Select a sub-area of the Results grid
        args:
            x_range - iterable of floats, two values representing the range of
                      x values to include in the zoomed grid, if input is
                      implicitly False all values are included (no x zooming)
            y_range - iterable of floats, two values representing the range of
                      y values to include in the zoomed grid, if input is
                      implicitly False all values are included (no y zooming)
        optional args:
            inplace - bool, if True the Results grid is changed in place,
                      otherwise a new Results is returned with the zoomed grid
            rereference - bool or number, if a number, the spatial grids will
                          be rereferenced to begin at that value. If True, the
                          spatial grids are rereferenced to begin at zero."""
        #check the ranges
        if(x_range is False):
            x_range = (self.xmin, self.xmax)
        if(y_range is False):
            y_range = (self.ymin, self.ymax)
        x_range, y_range = sorted(x_range), sorted(y_range)
        p1, p2 = (x_range[0], y_range[0]), (x_range[1], y_range[1])
        if((not self.in_grid(p1[0], p1[1]) or (not self.in_grid(p2[0], p2[1])))):
            raise(EMFError('Cannot zoom outside the results grid limits. The x limits are [%g, %g] and the y limits are [%g, %g].' % (self.xmin, self.xmax, self.ymin, self.ymax)))
        #get variables
        if(inplace):
            res = self
        else:
            res = self.copy()
        x, y = res.x, res.y
        #zoom
        bx = (x <= max(x_range)) & (x >= min(x_range))
        by = (y <= max(y_range)) & (y >= min(y_range))
        for k in res._grid:
            res._grid[k] = res._grid[k][by,:][:,bx]
        #check rereferencing
        if((type(rereference) is int) or (type(rereference) is float)):
            res.rereference(rereference, inplace=True)
        elif(rereference):
            res.rereference(inplace=True)
        if(not inplace):
            return(res)

    def flatten(self):
        """Create 1 dimensional versions of the gridded X, Y, and B arrays
        returns:
            x - 1D numpy array with x coordinates
            y - 1D numpy array with y coordinates
            b - 1D numpy array with magnetic field values"""
        nrows, ncols = self.B.shape
        n = nrows*ncols
        x = np.reshape(self.X, n)
        y = np.reshape(self.Y, n)
        b = np.reshape(self.B, n)
        return(x, y, b)

    def export(self, **kw):
        """Export the grid data and accompanying info to an excel file with tabs for each Bfield component, another for the info dict, and a final one for footprints if they're present
        kw:
            path - string, output destination/filename for workbook"""
        #get appropriate export filename
        fn = subcalc_funks._path_manage(self.name, '.xlsx', **kw)
        #create excel writing object
        xl = pd.ExcelWriter(fn, engine='xlsxwriter')
        #write grid data
        for k in self._grid:
            if((k != 'X') and (k != 'Y')):
                pd.DataFrame(self._grid[k], columns=self.x, index=self.y
                        ).to_excel(xl, sheet_name=k)
        #write results information if present
        if(self.info is not None):
            pd.DataFrame([self.info[k] for k in self.info], index=self.info.keys(),
                    columns=['Parameter Value']).sort_index().to_excel(
                            xl, sheet_name='info', index_label='Parameter Name')
        #write footprint DataFrame if present
        if(self.footprint_df is not None):
            self.footprint_df.to_excel(xl, sheet_name='footprints', index=False)
        #save and print
        xl.save()
        print('results saved to: %s' % fn)

    def copy(self):
        'Return a deep copy of the Results object'
        return(copy.deepcopy(self))

class Footprint(object):

    def __init__(self, name, x, y, power_line, of_concern, draw_as_loop, group):
        """
        args:
            name - string, the name of the Footprint, i.e. "Substation"
            x - iterable, x coordinates of Footprint
            y - iterable, y coordinates of Footprint
            power_line - bool, True indicates the footprint corresponds to
                         a modeled power line or circuit
            of_concern - bool, True if the Footprint represents an area
                         that is potentially concerned about EMF (homes)
            draw_as_loop - bool, True if the footprint should be plotted
                           as a closed loop
            group - string, group strings that are identical between
                    Footprint objects designate them as part of the same
                    group for plotting"""
        #check x and y are the same length
        if(len(x) != len(y)):
            raise(EMFError("""
            Footprints must have the same number of x and y values to form
            spatial coordinates"""))
        #set attributes
        self.name = str(name) #string
        self._x = [float(i) for i in x]
        self._y = [float(i) for i in y]
        self.power_line = bool(power_line) #bool
        self.of_concern = bool(of_concern) #bool
        self.draw_as_loop = bool(draw_as_loop) #bool
        self._group = group #string

    def _get_x(self):
        if(self.draw_as_loop):
            return(self._x + [self._x[0]])
        else:
            return(list(self._x))
    def _set_x(self, value):
        self._x = value
    x = property(_get_x, _set_x, None, 'x coordinates of Footprint vertices')

    def _get_y(self):
        if(self.draw_as_loop):
            return(self._y + [self._y[0]])
        else:
            return(list(self._y))
    def _set_y(self, value):
        self._y = value
    y = property(_get_y, _set_y, None, 'y coordinates of Footprint vertices')

    def _get_group(self):
        if(pd.isnull(self._group) or (self._group is None)):
            return('')
        else:
            return(self._group)
    def _set_group(self, value):
        self._group = value
    group = property(_get_group, _set_group, None, 'Group name')

    def __str__(self):
        """quick and dirty printing"""
        v = vars(self)
        keys = v.keys()
        s = '\n'
        for k in keys:
            s += str(k) + ': ' + str(v[k]) + '\n'
        return(s)
