# coding=utf-8
from __future__ import division

from .legend import Legend, LegendParameters

from .datatype.base import DataTypeBase

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.plane import Plane


class GraphicContainer(object):
    """Graphic container used to get legends, title locations, and colors for any graphic.

    Properties:
        values
        min_point
        max_point
        legend_parameters
        data_type
        unit
        legend
        value_colors
        lower_title_location
        upper_title_location
    """

    def __init__(self, values, min_point, max_point,
                 legend_parameters=None, data_type=None, unit=None):
        """Initialize graphic container.

        Args:
            values: A List or Tuple of numerical values that will be used to
                generate the legend and colors.
            min_point: A Point3D object for the minimum of the bounding box
                around the graphic geometry.
            max_point: A Point3D object for the maximum of the  bounding box
                around the graphic geometry.
            legend_parameters: An Optional LegendParameter object to override
                default parameters of the legend.
            data_type: Optional DataType from the ladybug datatype module, which
                will be used to assign default legend properties. (ie. Temperature())
            unit: Optional text string for the units of the values. (ie. 'C')
        """
        # check the inputs
        assert isinstance(min_point, Point3D), \
            'min_point should be a ladybug Point3D. Got {}'.format(type(min_point))
        assert isinstance(max_point, Point3D), \
            'max_point should be a ladybug Point3D. Got {}'.format(type(max_point))
        self._legend = Legend(values, legend_parameters)
        self._min_point = min_point
        self._max_point = max_point

        # set default legend parameters based on input data_type and unit
        self._data_type = data_type
        self._unit = unit
        if data_type is not None:
            # TODO: Have data types reference Colorsets, which override default colors
            assert isinstance(data_type, DataTypeBase), \
                'data_type should be a ladybug DataType. Got {}'.format(type(data_type))
            if self.legend_parameters.is_title_default:
                unit = data_type.units[0] if unit is None else unit
                data_type.is_unit_acceptable(unit)
                self.legend_parameters.title = unit if \
                    self.legend_parameters.vertical is True \
                    else '{} ({})'.format(data_type.name, unit)
            if data_type.unit_descr is not None and \
                    self.legend_parameters.ordinal_dictionary is None:
                self.legend_parameters.ordinal_dictionary = data_type.unit_descr
                sorted_keys = sorted(data_type.unit_descr.keys())
                if self.legend.is_min_default is True:
                    self.legend_parameters.min = sorted_keys[0]
                if self.legend.is_max_default is True:
                    self.legend_parameters.max = sorted_keys[-1]
                if self.legend_parameters.is_segment_count_default:
                    try:  # try to set the number of segments to align with ordinal text
                        min_i = sorted_keys.index(self.legend_parameters.min)
                        max_i = sorted_keys.index(self.legend_parameters.max)
                        self.legend_parameters.segment_count = \
                            len(sorted_keys[min_i:max_i + 1])
                    except IndexError:
                        pass
        elif unit is not None and self.legend_parameters.is_title_default:
            assert isinstance(unit, str), \
                'Expected string for unit. Got {}.'.format(type(unit))
            self.legend_parameters.title = unit

        # set the default segment_height
        if self.legend_parameters.is_segment_height_default:
            if self.legend_parameters.vertical:
                seg_height = float((self._max_point.y - self._min_point.y) / 20)
            else:
                seg_height = float((self._max_point.x - self._min_point.x) / 20)
            self.legend_parameters.segment_height = seg_height

        # set the default base point
        if self.legend_parameters.is_base_plane_default:
            if self.legend_parameters.vertical:
                base_pt = Point3D(
                    self._max_point.x + self.legend_parameters.segment_width,
                    self._min_point.y, self._min_point.z)
            else:
                base_pt = Point3D(
                    self._max_point.x, self._max_point.y +
                    3 * self.legend_parameters.text_height,
                    self._min_point.z)
            self.legend_parameters.base_plane = Plane(o=base_pt)

    @classmethod
    def from_dict(cls, data):
        """Create a graphic container from a dictionary.

        Args:
            data: {
            "values": (0, 10),
            "min_point": {"x": 0, "y": 0, "z": 0},
            "max_point": {"x": 10, "y": 10, "z": 0}],
            "legend_parameters": None,
            "data_type": None,
            "unit": None}
        """
        optional_keys = ('legend_parameters', 'data_type', 'unit')
        for key in optional_keys:
            if key not in data:
                data[key] = None
        legend_parameters = None
        if data['legend_parameters'] is not None:
            legend_parameters = LegendParameters.from_dict(data['legend_parameters'])
        data_type = None
        if data['data_type'] is not None:
            data_type = DataTypeBase.from_dict(data['data_type'])

        return cls(data['values'], Point3D.from_dict(data['min_point']),
                   Point3D.from_dict(data['max_point']),
                   legend_parameters, data_type, data['unit'])

    @property
    def values(self):
        """The assigned data set of values."""
        return self._legend.values

    @property
    def min_point(self):
        """Point3D for the minimum of the bounding box around referenced geometry."""
        return self._min_point

    @property
    def max_point(self):
        """Point3D for the maximum of the bounding box around referenced geometry."""
        return self._max_point

    @property
    def legend_parameters(self):
        """The legend parameters assigned to this graphic."""
        return self._legend._legend_par

    @property
    def data_type(self):
        """The data_type input to this object (if it exists)."""
        return self._data_type

    @property
    def unit(self):
        """The unit input to this object (if it exists)."""
        return self._unit

    @property
    def legend(self):
        """The legend assigned to this graphic."""
        return self._legend

    @property
    def value_colors(self):
        """A List of colors associated with the assigned values."""
        return self._legend.value_colors

    @property
    def lower_title_location(self):
        """A Plane for the lower location of title text."""
        return Plane(o=Point3D(
            self._min_point.x,
            self._min_point.y - 2.5 * self._legend.legend_parameters.text_height,
            self._min_point.z))

    @property
    def upper_title_location(self):
        """A Plane for the upper location of title text."""
        return Plane(o=Point3D(
            self._min_point.x,
            self._max_point.y + self._legend.legend_parameters.text_height,
            self._min_point.z))

    def to_dict(self):
        """Get result graphic container as a dictionary."""
        data_type = None if self.data_type is None else self.data_type.to_dict()
        return {
            'values': self.values,
            'min_point': self.min_point.to_dict(),
            'max_point': self.max_point.to_dict(),
            'legend_parameters': self.legend_parameters.to_dict(),
            'data_type': data_type,
            'unit': self.unit,
            'type': 'GraphicContainer'
        }

    def __len__(self):
        """Return length of values on the object."""
        return len(self._legend._values)

    def __getitem__(self, key):
        """Return one of the values."""
        return self._legend._values[key]

    def __iter__(self):
        """Iterate through the values."""
        return iter(self._legend._values)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """ResultMesh representation."""
        return 'Ladybug Result Mesh ({} values)'.format(len(self))
