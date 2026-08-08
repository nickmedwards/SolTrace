class Point:
    """
    A simple class to manage points in Cartesian coordinates.
    """
    def __init__(self, x=0, y=0, z=0):
        """
        Parameters
        ==========
        x : float
            x-coordinate
        y : float
            y-coordinate
        z : float
            z-coordinate
        """
        ## (float) x-coordinate
        self.x = x
        ## (float) y-coordinate
        self.y = y
        ## (float) z-coordinate
        self.z = z
        return
    def copy(self):
        pnew = Point()
        c = self.__dict__.copy()
        for attr in self.__dict__.keys():
            pnew.__setattr__(attr, c[attr])
        return pnew
    def __str__(self):
        return "[{:f}, {:f}, {:f}]".format(self.x, self.y, self.z)
    def __add__(self, obj):
        """
        Add to the current point coordinate values.

        Parameters
        ==========
        obj : variant
            If obj = (Point), adds component-wise to the current point
            If obj = (float), adds obj to each component
        Returns
        =======
        Point
            Reference to this point
        """
        if isinstance(obj, Point):
            return Point(self.x + obj.x, self.y + obj.y, self.z + obj.z)
        elif isinstance(obj, float):
            return Point(self.x + obj, self.y + obj, self.z + obj)
        else:
            raise ValueError("Invalid addition operator object")
        return self
    def __sub__(self, obj):
        """
        Subtract from the current point coordinate values.

        Parameters
        ==========
        obj : variant
            If obj = (Point), subtracts component-wise from the current point
            If obj = (float), subtracts obj from each component
        Returns
        =======
        Point
            Reference to this point
        """
        if isinstance(obj, Point):
            return Point(self.x - obj.x, self.y - obj.y, self.z - obj.z)
        elif isinstance(obj, float):
            return Point(self.x - obj, self.y - obj, self.z - obj)
        else:
            raise ValueError("Invalid subtraction operator object")
        return self
    def __mul__(self, obj):
        """
        Multiplies the current point coordinate values.

        Parameters
        ==========
        obj : variant
            If obj = (Point), multiplies the current point component-wise by obj
            If obj = (float), multiplies each component of the current point by obj
        Returns
        =======
        Point
            Reference to this point
        """
        if isinstance(obj, (float,int)):
            return Point(self.x*obj, self.y*obj, self.z*obj)
        else:
            raise ValueError("Invalid multiplication operator object")
    def __floordiv__(self, obj):
        """
        Divides the current point coordinate values, taking the floor of the result.

        Parameters
        ==========
        obj : variant
            If obj = (Point), divides current point component-wise
            If obj = (float), divides components of current point by obj
        Returns
        =======
        Point
            Reference to this point
        """
        if isinstance(obj, (float,int)):
            return Point(self.x//obj, self.y//obj, self.z//obj)
        else:
            raise ValueError("Invalid division operator object")
    def __truediv__(self, obj):
        """
        Divides the current point coordinate values/

        Parameters
        ==========
        obj : variant
            If obj = (Point), divides current point component-wise
            If obj = (float), divides components of current point by obj
        Returns
        =======
        Point
            Reference to this point
        """
        if isinstance(obj, (float,int)):
            return Point(self.x/obj, self.y/obj, self.z/obj)
        else:
            raise ValueError("Invalid division operator object")
    def radius(self):
        """
        Computes distance between current point and the origin (0,0,0)

        Returns
        =======
        float
            Calculated radius
        """
        mag = (self.x*self.x + self.y*self.y + self.z*self.z)**0.5
        return mag
    def unitize(self, inplace : bool = False):
        """
        Converts current point into a unit vector with magnitude 1

        Parameters
        ==========
        inplace : bool = False
            Specifies whether the current point is converted to a unit vector in place, or whether the
            current point remains unchanged and a unitized copy of the vector is returned.
        """
        mag = self.radius()
        if mag > 0:
            if inplace:
                self.x /= mag
                self.y /= mag
                self.z /= mag
            else:
                return Point(self.x/mag, self.y/mag, self.z/mag)

    def as_list(self):
        """
        Returns:
        --------
        coordinates as a python list [x,y,z]
        """
        return [self.x, self.y, self.z]