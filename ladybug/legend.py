# coding=utf-8
from __future__ import division

from .color import Color, Colorset, ColorRange

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.mesh import Mesh3D
from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.mesh import Mesh2D

try:
    from collections.abc import Iterable  # python < 3.7
except ImportError:
    from collections import Iterable  # python >= 3.8
import sys
if (sys.version_info > (3, 0)):  # python 3
    xrange = range


class Legend(object):
    """Ladybug legend used to get legend geometry, legend text, generate colors, etc.

    Properties:
        legend_parameters
        values
        value_colors
        title
        title_location
        title_location_2d
        segment_text
        segment_text_location
        segment_text_location_2d
        segment_mesh
        segment_mesh_2d
        color_range
        segment_numbers
        segment_colors
        segment_length
        is_min_default
        is_max_default

    Usage:
        ##
        data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        legend = Legend(data, LegendParameters(segment_count=6))
        print(legend.segment_text)
        print(legend.segment_mesh)
        print(legend.segment_colors)

        >> ['0.00', '1.80', '3.60', '5.40', '7.20', '9.00']
        >> Mesh3D (6 faces) (14 vertices)
        >> ((R:75, G:107, B:169), (R:159, G:189, B:238), (R:224, G:229, B:145),
            (R:247, G:200, B:53), (R:234, G:113, B:0), (R:234, G:38, B:0))

        ##
        data = [100, 300, 500, 1000, 2000, 3000]
        legend_par = LegendParameters(min=300, max=2000, segment_count=3)
        legend_par.ordinal_dictionary = {300: 'low', 1150: 'desired', 2000: 'too much'}
        legend = Legend(data, legend_par)
        print(legend.segment_text)
        print(legend.segment_mesh)
        print(legend.segment_colors)
        print(legend.value_colors)  # colors in between dict categories are interpolated
        legend.legend_parameters.continuous_colors = False  # get data in only 3 colors
        print(legend.value_colors)  # data colors align with segment_count

        >> ['low', 'desired', 'too much']
        >> Mesh3D (3 faces) (8 vertices)
        >> ((R:75, G:107, B:169), (R:249, G:235, B:89), (R:234, G:38, B:0))
        >> ((R:75, G:107, B:169), (R:75, G:107, B:169), (R:118, G:150, B:205),
            (R:230, G:231, B:134), (R:234, G:38, B:0), (R:234, G:38, B:0))
        >> ((R:75, G:107, B:169), (R:115, G:147, B:202), (R:115, G:147, B:202),
            (R:115, G:147, B:202), (R:115, G:147, B:202), (R:234, G:38, B:0))

        ##
        data = [-0.5, 0, 0.5]
        legend_par = LegendParameters(min=-1, max=1, segment_count=3)
        legend_par.ordinal_dictionary = {-3: 'Cold', -2: 'Cool', -1: 'Slightly Cool',
                                         0: 'Neutral',
                                         1: 'Slightly Warm', 2: 'Warm', 3: 'Hot'}
        legend = Legend(data, legend_par)
        print(legend.segment_text)
        print(legend.segment_mesh)
        print(legend.segment_colors)
        legend.legend_parameters.segment_count = 5
        print(legend.segment_text)
        legend.legend_parameters.min = -2
        legend.legend_parameters.max = 2
        print(legend.segment_text)
        >> ['Slightly Cool', 'Neutral', 'Slightly Warm']
        >> Mesh3D (3 faces) (8 vertices)
        >> ((R:75, G:107, B:169), (R:249, G:235, B:89), (R:234, G:38, B:0))
        >> ['Slightly Cool', '', 'Neutral', '', 'Slightly Warm']
        >> ['Cool', 'Slightly Cool', 'Neutral', 'Slightly Warm', 'Warm']
    """

    def __init__(self, values, legend_parameters=None):
        """Initalize Ladybug Legend.

        Args:
            values: A List or Tuple of numerical values that will be used to
                generate the legend and colors.
            legend_parameters: An Optional LegendParameter object to override
                default parameters of the legend.
            """
        # check the inputs
        assert isinstance(values, Iterable) \
            and not isinstance(values, (str, dict, bytes, bytearray)), \
            'values should be a list or tuple. Got {}'.format(type(values))
        self._values = values
        if legend_parameters is not None:
            assert isinstance(legend_parameters, LegendParameters), \
                'Expected LegendParameters. Got {}.'.format(type(legend_parameters))
            self._legend_par = legend_parameters.duplicate()
        else:
            self._legend_par = LegendParameters()

        # set default min, max and (if horizontal) segment width
        self._is_min_default = False
        self._is_max_default = False
        if self._legend_par.min is None:
            self._legend_par.min = min(values)
            self._is_min_default = True
        if self._legend_par.max is None:
            self._legend_par.max = max(values)
            self._is_max_default = True
        if not self._legend_par.vertical and self._legend_par.is_segment_width_default:
            self._legend_par.segment_width = self._legend_par.text_height * \
                (len(str(int(self._legend_par.max))) +
                 self._legend_par.decimal_count + 2)

    @classmethod
    def from_dict(cls, data):
        """Create a legend from a dictionary.

        Args:
            data: {
            "values": (0, 10),
            "legend_parameters": None}
        """
        if 'legend_parameters' not in data:
            data['legend_parameters'] = None
        legend_parameters = None
        if data['legend_parameters'] is not None:
            legend_parameters = LegendParameters.from_dict(data['legend_parameters'])
        for key in ('is_min_default', 'is_max_default'):
            if key not in data:
                data[key] = False

        legend = cls(data['values'], legend_parameters)
        legend._is_min_default = data['is_min_default']
        legend._is_max_default = data['is_max_default']
        return legend

    @property
    def legend_parameters(self):
        """The legend parameters assigned to this legend."""
        return self._legend_par

    @property
    def values(self):
        """The data set assigned to the legend."""
        return self._values

    @property
    def value_colors(self):
        """A List of colors associated with the assigned values."""
        _color_range = self.color_range
        return tuple(_color_range.color(val) for val in self.values)

    @property
    def title(self):
        """A text string for the title of the legend."""
        return self.legend_parameters.title

    @property
    def title_location(self):
        """A Plane for the location and orientation of the legend title."""
        _base_pl = self.legend_parameters.base_plane
        _title_pt = self._title_point_2d()
        return Plane(_base_pl.n, _base_pl.xy_to_xyz(_title_pt), _base_pl.x)

    @property
    def title_location_2d(self):
        """A Point2D for the location of the title.

        Useful for output to 2D interfaces.
        """
        _base_o = self.legend_parameters.base_plane.o
        _title_pt = self._title_point_2d()
        return Point2D(_title_pt.x + _base_o.x, _title_pt.y + _base_o.y)

    @property
    def segment_text(self):
        """A list of text strings for the segment labels of the legend."""
        _l_par = self.legend_parameters
        if _l_par.ordinal_dictionary is None:
            format_str = '%.{}f'.format(_l_par.decimal_count)
            seg_txt = [format_str % x for x in self.segment_numbers]
            if _l_par.include_larger_smaller:
                seg_txt[0] = '<' + seg_txt[0]
                seg_txt[-1] = '>' + seg_txt[-1]
            return seg_txt
        else:
            seg_txt = []
            for x in self.segment_numbers:
                try:
                    seg_txt.append(_l_par.ordinal_dictionary[x])
                except KeyError:
                    seg_txt.append('')
        return seg_txt

    @property
    def segment_text_location(self):
        """A list of Plane objects for the location of the legend segment text."""
        _base_pl = self.legend_parameters.base_plane
        _pt_2d = self._segment_point_2d()
        return [Plane(_base_pl.n, _base_pl.xy_to_xyz(pt), _base_pl.x) for pt in _pt_2d]

    @property
    def segment_text_location_2d(self):
        """A list of Point2D for the location of the legend segment text.

        Useful for output to 2D interfaces.
        """
        _base_o = self.legend_parameters.base_plane.o
        _pt_2d = self._segment_point_2d()
        return [Point2D(pt.x + _base_o.x, pt.y + _base_o.y) for pt in _pt_2d]

    @property
    def segment_mesh(self):
        """A Ladybug Mesh3D for the legend colors."""
        _mesh_2d = self._segment_mesh_2d()
        return Mesh3D.from_mesh2d(_mesh_2d, self.legend_parameters.base_plane)

    @property
    def segment_mesh_2d(self):
        """A Ladybug Mesh2D for the legend colors."""
        _o = self.legend_parameters.base_plane.o
        return self._segment_mesh_2d(Point2D(_o.x, _o.y))

    @property
    def color_range(self):
        """The color range associated with this legend."""
        _l_par = self.legend_parameters
        return ColorRange(_l_par.colors, (_l_par.min, _l_par.max),
                          _l_par.continuous_colors)

    @property
    def segment_numbers(self):
        _l_par = self.legend_parameters
        _seg_stp = (_l_par.max - _l_par.min) / (_l_par.segment_count - 1)
        return tuple(_l_par.min + i * _seg_stp
                     for i in xrange(_l_par.segment_count))

    @property
    def segment_colors(self):
        """A List of colors associated with the legend segments."""
        _color_range = self.color_range
        return tuple(_color_range.color(val) for val in self.segment_numbers)

    @property
    def segment_length(self):
        """An integer for the number of segment lengths in the legend."""
        _l_par = self.legend_parameters
        return _l_par.segment_count if not _l_par.continuous_legend else \
            _l_par.segment_count - 1

    @property
    def is_min_default(self):
        """Boolean noting whether the min is default.

        Useful when deciding whether to override the legend to properly display an
        ordinal dictionary.
        """
        return self._is_min_default

    @property
    def is_max_default(self):
        """Boolean noting whether the max is default.

        Useful when deciding whether to override the legend to properly display an
        ordinal dictionary.
        """
        return self._is_max_default

    def duplicate(self):
        """Return a copy of the current legend."""
        return self.__copy__()

    def to_dict(self):
        """Get legend as a dictionary."""
        return {
            'values': self.values,
            'legend_parameters': self.legend_parameters.to_dict(),
            'is_min_default': self.is_min_default,
            'is_max_default': self.is_max_default,
            'type': 'Legend'
        }

    def _title_point_2d(self):
        """Point2D for the title in the 2D space of the legend."""
        _l_par = self.legend_parameters
        if _l_par.vertical:
            offset = 0.5 if self.legend_parameters.continuous_legend is True else 0.25
            return Point2D(0, _l_par.segment_height * (self.segment_length + offset))
        else:
            return Point2D(-_l_par.segment_width * self.segment_length,
                           _l_par.segment_height * 1.25)

    def _segment_point_2d(self):
        """Point2D for the segment text in the 2D space of the legend."""
        _l_par = self.legend_parameters
        if _l_par.vertical:  # vertical
            _pt_2d = tuple(
                Point2D(_l_par.segment_width + _l_par.text_height * 0.25, i)
                for i in Legend._frange(0, _l_par.segment_height *
                                        _l_par.segment_count,
                                        _l_par.segment_height))
        else:  # horizontal
            _start_val = -_l_par.segment_width * self.segment_length
            _pt_2d = tuple(
                Point2D(_start_val + i, -_l_par.text_height * 1.25)
                for i in Legend._frange(0, _l_par.segment_width *
                                        _l_par.segment_count,
                                        _l_par.segment_width))
        return _pt_2d

    def _segment_mesh_2d(self, base_pt=Point2D(0, 0)):
        """Mesh2D for the segments in the 2D space of the legend."""
        # get general properties
        _l_par = self.legend_parameters
        n_seg = self.segment_length
        # create the 2D mesh of the legend
        if _l_par.vertical:
            mesh2d = Mesh2D.from_grid(
                base_pt, 1, n_seg, _l_par.segment_width, _l_par.segment_height)
        else:
            _base_pt = Point2D(base_pt.x - _l_par.segment_width * n_seg, base_pt.y)
            mesh2d = Mesh2D.from_grid(
                _base_pt, n_seg, 1, _l_par.segment_width, _l_par.segment_height)
        # add colors to the mesh
        _seg_colors = self.segment_colors
        if not _l_par.continuous_legend:
            mesh2d.colors = _seg_colors
        else:
            if _l_par.vertical:
                mesh2d.colors = _seg_colors + _seg_colors
            else:
                mesh2d.colors = tuple(col for col in _seg_colors for i in (0, 1))
        return mesh2d

    @staticmethod
    def _frange(start, stop, step):
        """Range function capable of yielding float values."""
        while start < stop:
            yield start
            start += step

    def __copy__(self):
        _leg = Legend(self.values, self.legend_parameters)
        _leg._is_min_default = self._is_min_default
        _leg._is_max_default = self._is_max_default
        return _leg

    def __len__(self):
        """Return length of values on the object."""
        return len(self._values)

    def __getitem__(self, key):
        """Return one of the values."""
        return self._values[key]

    def __iter__(self):
        """Iterate through the values."""
        return iter(self._values)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Legend representation."""
        return 'Ladybug Legend ({} values)'.format(len(self))


class LegendParameters(object):
    """Ladybug legend parameters used to customize legends.

    All properties of LegendParameters are set-able (except the is_..._default ones).

    Properties:
        min
        max
        segment_count
        colors
        continuous_colors
        continuous_legend
        title
        ordinal_dictionary
        decimal_count
        include_larger_smaller
        vertical
        base_plane
        segment_height
        segment_width
        text_height
        font

        is_segment_count_default
        is_title_default
        is_base_plane_default
        is_segment_height_default
        is_segment_width_default
        is_text_height_default

    Usage:
        ##
        lp = LegendParameters(min=0, max=100, segment_count=6)
        lp.vertical = False
        lp.segment_width = 5
    """

    def __init__(self, min=None, max=None, segment_count=None,
                 colors=None, title=None, base_plane=None):
        """Initalize Ladybug Legend Parameters.

        Args:
            min: A number to set the lower boundary of the legend. If None, the
                minimum of the values associated with the legend will be used.
            max: A number to set the upper boundary of the legend. If None, the
                maximum of the values associated with the legend will be used.
            segment_count: An interger representing the number of steps between
                the high and low boundary of the legend. The default is set to 11
                and any custom values input in here should always be greater than or
                equal to 2.
            colors: An list of color objects. Default is Ladybug's original colorset.
            title: Text string for Legend title. Typically, the units of the data are
                used here but the type of data might also be used. Default is
                an empty string.
            base_plane: A Ladybug Plane object to note the starting point from
                where the legend will be genrated. The default is the world XY plane
                at origin (0, 0, 0).
        """
        self._min = None
        self._max = None
        self.min = min
        self.max = max
        self.segment_count = segment_count
        self.colors = colors
        self.title = title
        self.base_plane = base_plane

        self.continuous_colors = None
        self.continuous_legend = None
        self.ordinal_dictionary = None
        self.decimal_count = None
        self.include_larger_smaller = None
        self.vertical = None
        self.segment_height = None
        self.segment_width = None
        self.text_height = None
        self.font = None

    @classmethod
    def from_dict(cls, data):
        """Create a color range from a dictionary.

        Args:
            data: {
            "min": -3,
            "max": 3,
            "segment_count": 7}
        """
        optional_keys = ('min', 'max', 'segment_count',
                         'colors', 'continuous_colors', 'continuous_legend',
                         'title', 'ordinal_dictionary',
                         'decimal_count', 'include_larger_smaller',
                         'vertical', 'base_plane', 'segment_height',
                         'segment_width', 'text_height', 'font')
        default_keys = ('is_segment_count_default', 'is_title_default',
                        'is_base_plane_default', 'is_segment_height_default',
                        'is_segment_width_default', 'is_text_height_default')
        for key in optional_keys:
            if key not in data:
                data[key] = None
        for key in default_keys:
            if key not in data:
                data[key] = False

        colors = None
        if data['colors'] is not None:
            colors = [Color.from_dict(col) for col in data['colors']]
        base_plane = None
        if data['base_plane'] is not None:
            base_plane = Plane.from_dict(data['base_plane'])

        leg_par = cls(data['min'], data['max'], data['segment_count'],
                      colors, data['title'], base_plane)
        leg_par.continuous_colors = data['continuous_colors']
        leg_par.continuous_legend = data['continuous_legend']
        leg_par.ordinal_dictionary = data['ordinal_dictionary']
        leg_par.decimal_count = data['decimal_count']
        leg_par.include_larger_smaller = data['include_larger_smaller']
        leg_par.vertical = data['vertical']
        leg_par.segment_height = data['segment_height']
        leg_par.segment_width = data['segment_width']
        leg_par.text_height = data['text_height']
        leg_par.font = data['font']
        leg_par._is_segment_count_default = data['is_segment_count_default']
        leg_par._is_title_default = data['is_title_default']
        leg_par._is_base_plane_default = data['is_base_plane_default']
        leg_par._is_segment_height_default = data['is_segment_height_default']
        leg_par._is_segment_width_default = data['is_segment_width_default']
        leg_par._is_text_height_default = data['is_text_height_default']
        return leg_par

    @property
    def min(self):
        """Get or set legend minimum."""
        return self._min

    @min.setter
    def min(self, minimum):
        if minimum is not None:
            assert isinstance(minimum, (float, int)), \
                'Expected number for min. Got {}.'.format(type(minimum))
            if self._max is not None:
                assert minimum <= self._max, \
                    'Input min is greater than input max. {} > {}.'.format(
                        minimum, self._max)
        self._min = minimum

    @property
    def max(self):
        """Get or set legend maximum."""
        return self._max

    @max.setter
    def max(self, maximum):
        if maximum is not None:
            assert isinstance(maximum, (float, int)), \
                'Expected number for max. Got {}.'.format(type(maximum))
            if self._min is not None:
                assert maximum >= self._min, \
                    'Input max is less than input min. {} < {}.'.format(
                        maximum, self._min)
        self._max = maximum

    @property
    def segment_count(self):
        """Get or set the number of segments in the legend."""
        return self._segment_count

    @segment_count.setter
    def segment_count(self, nos):
        if nos is not None:
            assert isinstance(nos, int), \
                'Expected integer for segment_count. Got {}.'.format(type(nos))
            assert nos >= 2, 'segment_count must be greater or equal to 2.' \
                ' Got {}.'.format(nos)
            self._segment_count = nos
            self._is_segment_count_default = False
        else:
            self._segment_count = 11
            self._is_segment_count_default = True

    @property
    def colors(self):
        """Get or set the colors defining the legend."""
        return self._colors

    @colors.setter
    def colors(self, cols):
        if cols is not None:
            assert isinstance(cols, Iterable) \
                and not isinstance(cols, (str, dict, bytes, bytearray)), \
                'Colors should be a list or tuple. Got {}'.format(type(cols))
            assert len(cols) > 1, 'There must be at least two colors to make a legend.'
            try:
                cols = tuple(col if isinstance(col, Color) else Color(
                    col.R, col.G, col.B) for col in cols)
            except Exception:
                try:
                    cols = tuple(Color(col.Red, col.Green, col.Blue)
                                 for col in cols)
                except Exception:
                    raise ValueError("{} is not a valid list of colors".format(cols))
            self._colors = cols
        else:
            self._colors = Colorset.original()

    @property
    def continuous_colors(self):
        """Boolean noting whether colors generated are continuous or discrete.

        If True, the colors generated from the corresponding legend will be in a
        continuous gradient. If False, they will be categorized in incremental
        groups according to the segment_count. Default is True for continuous colors.
        """
        return self._continuous_colors

    @continuous_colors.setter
    def continuous_colors(self, cont_cols):
        if cont_cols is not None:
            assert isinstance(cont_cols, bool), \
                'Expected boolean for continuous_colors. Got {}.'.format(type(cont_cols))
            self._continuous_colors = cont_cols
        else:
            self._continuous_colors = True

    @property
    def continuous_legend(self):
        """Boolean noting whether legend is drawn as a gradient or discrete segments.

        If True, the legend mesh will be drawn vertex-by-vertex resulting in a
        continuous gradient instead of discrete segments. If False, the mesh will be
        generated with one face for each of the segment_counts.
        Default is False for depicting discrete categories.
        """
        return self._continuous_legend

    @continuous_legend.setter
    def continuous_legend(self, cont_leg):
        if cont_leg is not None:
            assert isinstance(cont_leg, bool), \
                'Expected boolean for continuous_legend. Got {}.'.format(type(cont_leg))
            self._continuous_legend = cont_leg
        else:
            self._continuous_legend = False

    @property
    def title(self):
        """Get or set the text for the title of the legend."""
        return self._title

    @title.setter
    def title(self, title):
        if title is not None:
            assert isinstance(title, str), \
                'Expected string for title. Got {}.'.format(type(title))
            self._title = title
            self._is_title_default = False
        else:
            self._title = ''
            self._is_title_default = True

    @property
    def ordinal_dictionary(self):
        """Get or set an optional dictionary that maps values to text categories.

        If None, numerical values will be usedfor the legend segments. If not, text
        categories will be used and the legend will be ordinal. Note that, if the
        number if items in the dictionary are less than the segment_count, some segments
        won't recieve any label. Examples for possible dictiionaries include:
        {-1: 'Cold', 0: 'Neutral', 1: 'Hot'}
        {0: 'False', 1: 'True'}
        """
        return self._ordinal_dictionary

    @ordinal_dictionary.setter
    def ordinal_dictionary(self, o_dict):
        if o_dict is not None:
            assert isinstance(o_dict, dict), \
                'Expected dictionary for ordinal_dictionary. Got {}.'.format(
                    type(o_dict))
            for key in o_dict.keys():
                assert isinstance(key, int), \
                    'Expected integer for ordinal_dictionary key. Got {}.'.format(
                        type(key))
        self._ordinal_dictionary = o_dict

    @property
    def decimal_count(self):
        """Get or set an integer for the number of decimal places in the legend text.

        Default is 2. Note that this input has no bearing on the resulting legend
        text when an ordinal_dictionary is present.
        """
        return self._decimal_count

    @decimal_count.setter
    def decimal_count(self, n_dec):
        if n_dec is not None:
            assert isinstance(n_dec, int), \
                'Expected integer for decimal_count. Got {}.'.format(type(n_dec))
            self._decimal_count = n_dec
        else:
            self._decimal_count = 2

    @property
    def include_larger_smaller(self):
        """Boolean noting whether > and < should be included in legend segment text.

         Default is False.
         """
        return self._include_larger_smaller

    @include_larger_smaller.setter
    def include_larger_smaller(self, lgsm):
        self._include_larger_smaller = bool(lgsm)

    @property
    def vertical(self):
        """Boolean noting whether legend is vertical (True) of horizontal (False).

        Default is True for a vertically-oriented legend.
        """
        return self._vertical

    @vertical.setter
    def vertical(self, vertical):
        if vertical is not None:
            assert isinstance(vertical, bool), \
                'Expected boolean for vertical. Got {}.'.format(
                    type(vertical))
            self._vertical = vertical
        else:
            self._vertical = True

    @property
    def base_plane(self):
        """Get or set a Ladybug Point3D for the base point of the legend."""
        return self._base_plane

    @base_plane.setter
    def base_plane(self, base_pl):
        if base_pl is not None:
            assert isinstance(base_pl, Plane), \
                'Expected Ladybug Plane for base_plane. Got {}.'.format(type(base_pl))
            self._base_plane = base_pl
            self._is_base_plane_default = False
        else:
            self._base_plane = Plane(Vector3D(0, 0, 1), Point3D(0, 0, 0))
            self._is_base_plane_default = True

    @property
    def segment_height(self):
        """Get or set the height for each of the legend segments.

         Default is 1.
        """
        return self._segment_height

    @segment_height.setter
    def segment_height(self, seg_h):
        if seg_h is not None:
            assert isinstance(seg_h, (float, int)), \
                'Expected number for segment_height. Got {}.'.format(type(seg_h))
            assert seg_h > 0, 'segment_height must be greater than 0.' \
                ' Got {}.'.format(seg_h)
            self._segment_height = seg_h
            self._is_segment_height_default = False
        else:
            self._segment_height = 1
            self._is_segment_height_default = True

    @property
    def segment_width(self):
        """Get or set the width for each of the legend segments.

         Default is 1 when legend is vertical. When horizontal, the default is
         text_height * (max_number_of_digits + 2) where max_number_of_digits is
         the number of digits displaying in the legend parameter max.
        """
        if not self.vertical and self.is_segment_width_default:
            return self.text_height * 5
        return self._segment_width

    @segment_width.setter
    def segment_width(self, seg_w):
        if seg_w is not None:
            assert isinstance(seg_w, (float, int)), \
                'Expected number for segment_width. Got {}.'.format(type(seg_w))
            assert seg_w > 0, 'segment_width must be greater than 0.' \
                ' Got {}.'.format(seg_w)
            self._segment_width = seg_w
            self._is_segment_width_default = False
        else:
            self._segment_width = 1
            self._is_segment_width_default = True

    @property
    def text_height(self):
        """Get or set the height for the legend text.

        Default is 1/3 of the segment_height.
        """
        if self.is_text_height_default:
            return self.segment_height * 0.33
        return self._text_height

    @text_height.setter
    def text_height(self, txt_h):
        if txt_h is not None:
            assert isinstance(txt_h, (float, int)), \
                'Expected number for text_height. Got {}.'.format(type(txt_h))
            assert txt_h > 0, 'text_height must be greater than 0.' \
                ' Got {}.'.format(txt_h)
            self._is_text_height_default = False
        else:
            self._is_text_height_default = True
        self._text_height = txt_h

    @property
    def font(self):
        """Get or set the font for the legend text.

        Examples include "Arial", "Times New Roman", "Courier". Note that this
        parameter may not have an effect on certain interfaces that have limited
        access to fonts. Default is "Arial".
        """
        return self._font

    @font.setter
    def font(self, font):
        if font is not None:
            assert isinstance(font, str), \
                'Expected string for font. Got {}.'.format(type(font))
            self._font = font
        else:
            self._font = 'Arial'

    @property
    def is_segment_count_default(self):
        """Boolean noting whether the number of segments is defaulted."""
        return self._is_segment_count_default

    @property
    def is_title_default(self):
        """Boolean noting whether the title is defaulted."""
        return self._is_title_default

    @property
    def is_base_plane_default(self):
        """Boolean noting whether the base point is defaulted."""
        return self._is_base_plane_default

    @property
    def is_segment_height_default(self):
        """Boolean noting whether the segment height is defaulted."""
        return self._is_segment_height_default

    @property
    def is_segment_width_default(self):
        """Boolean noting whether the segment width is defaulted."""
        return self._is_segment_width_default

    @property
    def is_text_height_default(self):
        """Boolean noting whether the text height is defaulted."""
        return self._is_text_height_default

    def duplicate(self):
        """Return a copy of the current legend parameters."""
        return self.__copy__()

    def to_dict(self):
        """Get legend parameters as a dictionary."""
        seg = None if self.is_segment_count_default else self.segment_count
        title = None if self.is_title_default else self.title
        base_plane = None if self.is_base_plane_default else self.base_plane.to_dict()
        seg_h = None if self.is_segment_height_default else self.segment_height
        seg_w = None if self.is_segment_width_default else self.segment_width
        txt_h = None if self.is_text_height_default else self.text_height
        return {
            'min': self.min, 'max': self.max, 'segment_count': seg,
            'colors': [col.to_dict() for col in self.colors],
            'continuous_colors': self.continuous_colors,
            'continuous_legend': self.continuous_legend, 'title': title,
            'ordinal_dictionary': self.ordinal_dictionary,
            'decimal_count': self.decimal_count,
            'include_larger_smaller': self.include_larger_smaller,
            'vertical': self.vertical,
            'base_plane': base_plane,
            'segment_height': seg_h, 'segment_width': seg_w,
            'text_height': txt_h, 'font': self.font,
            'is_segment_count_default': self.is_segment_count_default,
            'is_title_default': self.is_title_default,
            'is_base_plane_default': self.is_base_plane_default,
            'is_segment_height_default': self.is_segment_height_default,
            'is_segment_width_default': self.is_segment_width_default,
            'is_text_height_default': self.is_text_height_default,
            'type': 'LegendParameters'
        }

    def __copy__(self):
        new_par = LegendParameters(self.min, self.max, self.segment_count,
                                   self.colors, self.title, self.base_plane)
        new_par._continuous_colors = self._continuous_colors
        new_par._continuous_legend = self._continuous_legend
        new_par._ordinal_dictionary = self._ordinal_dictionary
        new_par._decimal_count = self._decimal_count
        new_par._include_larger_smaller = self._include_larger_smaller
        new_par._vertical = self._vertical
        new_par._segment_height = self._segment_height
        new_par._segment_width = self._segment_width
        new_par._text_height = self._text_height
        new_par._font = self._font
        new_par._is_segment_count_default = self._is_segment_count_default
        new_par._is_title_default = self._is_title_default
        new_par._is_base_plane_default = self._is_base_plane_default
        new_par._is_segment_height_default = self._is_segment_height_default
        new_par._is_segment_width_default = self._is_segment_width_default
        new_par._is_text_height_default = self._is_text_height_default
        return new_par

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Legend parameter representation."""
        min = self.min if self.min is not None else '[default]'
        max = self.max if self.max is not None else '[default]'
        seg = '[default]' if self.is_segment_count_default \
            else self.segment_count
        title = '[default]' if self.is_title_default else self.title
        base_pt = '[default]' if self.is_base_plane_default else self.base_plane.o
        seg_h = '[default]' if self.is_segment_height_default else self.segment_height
        seg_w = '[default]' if self.is_segment_width_default else self.segment_width
        txt_h = '[default]' if self.is_text_height_default else self.text_height
        return 'Legend Parameters\n minimum: {}\n maximum: {}\n segments: {}\n' \
            ' colors:\n  {}\n continuous colors: {}\n continuous legend: {}\n' \
            ' title: {}\n ordinal text: {}\n number decimals: {}\n' \
            ' include < >: {}\n vertical: {}\n base point:\n  {}\n' \
            ' segment height: {}\n segment width: {}\n' \
            ' text height: {}\n font: {}'.format(
                min, max, seg, '\n  '.join([str(c) for c in self.colors]),
                self.continuous_colors, self.continuous_legend, title,
                self.ordinal_dictionary, self.decimal_count,
                self.include_larger_smaller, self.vertical,
                base_pt, seg_h, seg_w, txt_h, self.font)
