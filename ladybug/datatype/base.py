# coding=utf-8
"""Base data type."""
from __future__ import division

from os.path import dirname, basename, isfile, join
from os import listdir
from importlib import import_module
import re


class DataTypeBase(object):
    """Base class for data types.

    Properties:
        name: The full name of the data type as a string.
        units: A list of all accetpable units of the data type as abbreviated text.
            The first item of the list should be the standard SI unit.
            The second item of the list should be the stadard IP unit (if it exists).
            The rest of the list can be any other acceptable units.
            (eg. [C, F, K])
        si_units: A list of acceptable SI units.
        ip_units: A list of acceptable IP units.
        min: Lower limit for the data type, values below which should be physically
            or mathematically impossible. (Default: -inf)
        max: Upper limit for the data type, values above which should be physically
            or mathematically impossible. (Default: +inf)
        abbreviation: An optional abbreviation for the data type as text.
            (eg. 'UTCI' for Universal Thermal Climate Index).
            This can also be a letter that represents the data type in a formula.
            (eg. 'A' for Area; 'P' for Pressure)
        unit_descr: An optional dictionary describing categories that the numerical
            values of the units relate to. For example:
            {-1: 'Cold', 0: 'Neutral', +1: 'Hot'}
            {0: 'False', 1: 'True'}
        point_in_time: Boolean to note whether the data type represents conditions
            at a single instant in time (True) as opposed to being an average or
            accumulation over time (False) when it is found in hourly lists of data.
            (True Examples: Temperature, WindSpeed)
            (False Examples: Energy, Radiation, Illuminance)
        cumulative: Boolean to tell whether the data type can be cumulative when it
            is represented over time (True) or it can only be averaged over time
            to be meaningful (False). Note that cumulative cannot be True
            when point_in_time is also True.
            (False Examples: Temperature, Irradiance, Illuminance)
            (True Examples: Energy, Radiation)
    """
    _name = None
    _units = [None]
    _si_units = [None]
    _ip_units = [None]
    _min = float('-inf')
    _max = float('+inf')

    _abbreviation = ''
    _unit_descr = None
    _point_in_time = True
    _cumulative = False

    _type_enumeration = None

    def __init__(self, name=None):
        """Initialize DataType.

        Args:
            name: Optional name for the type. Default is derived from the class name.
        """
        self._name = name

    @classmethod
    def from_dict(cls, data):
        """Create a data type from a dictionary.

        Args:
            data: Data as a dictionary.
                {
                    "name": data type name of the data type as a string
                    "data_type": the class name of the data type as a string
                    "base_unit": the base unit of the data type
                }
        """
        assert 'name' in data, 'Required keyword "name" is missing!'
        assert 'data_type' in data, 'Required keyword "data_type" is missing!'
        if cls._type_enumeration is None:
            cls._type_enumeration = _DataTypeEnumeration(import_modules=False)

        if data['data_type'] == 'GenericType':
            assert 'base_unit' in data, \
                'Keyword "base_unit" is missing and is required for GenericType.'
            return cls._type_enumeration._GENERICTYPE(data['name'], data['base_unit'])
        elif data['data_type'] in cls._type_enumeration._TYPES:
            clss = cls._type_enumeration._TYPES[data['data_type']]
            if data['data_type'] == data['name'].title().replace(' ', ''):
                return clss()
            else:
                instance = clss()
                instance._name = data['name']
                return instance
        else:
            raise ValueError(
                'Data Type {} could not be recognized'.format(data['data_type']))

    def is_unit_acceptable(self, unit, raise_exception=True):
        """Check if a certain unit is acceptable for the data type.

        Args:
            unit: A text string representing the abbreviated unit.
            raise_exception: Set to True to raise an exception if not acceptable.
        """
        _is_acceptable = unit in self.units

        if _is_acceptable or raise_exception is False:
            return _is_acceptable
        else:
            raise ValueError(
                '{0} is not an acceptable unit type for {1}. '
                'Choose from the following: {2}'.format(
                    unit, self.__class__.__name__, self.units
                )
            )

    def to_unit(self, values, unit, from_unit=None):
        """Return values converted to the unit given the input from_unit."""
        raise NotImplementedError(
            'to_unit is not implemented on %s' % self.__class__.__name__
        )

    def to_ip(self, values, from_unit=None):
        """Return values in IP and the units to which the values have been converted."""
        raise NotImplementedError(
            'to_ip is not implemented on %s' % self.__class__.__name__
        )

    def to_si(self, values, from_unit=None):
        """Return values in SI and the units to which the values have been converted."""
        raise NotImplementedError(
            'to_si is not implemented on %s' % self.__class__.__name__
        )

    def is_in_range(self, values, unit=None, raise_exception=True):
        """Check if a list of values is within physically/mathematically possible range.

        Args:
            values: A list of values.
            unit: The unit of the values.  If not specified, the default metric
                unit will be assumed.
            raise_exception: Set to True to raise an exception if not in range.
        """
        self._is_numeric(values)
        if unit is None or unit == self.units[0]:
            minimum = self.min
            maximum = self.max
        else:
            namespace = {'self': self}
            self.is_unit_acceptable(unit, True)
            min_statement = "self._{}_to_{}(self.min)".format(
                self._clean(self.units[0]), self._clean(unit))
            max_statement = "self._{}_to_{}(self.max)".format(
                self._clean(self.units[0]), self._clean(unit))
            minimum = eval(min_statement, namespace)
            maximum = eval(max_statement, namespace)

        for value in values:
            if value < minimum or value > maximum:
                if not raise_exception:
                    return False
                else:
                    raise ValueError(
                        '{0} should be between {1} and {2}. Got {3}'.format(
                            self.__class__.__name__, self.min, self.max, value
                        )
                    )
        return True

    def duplicate(self):
        """Return a copy of the data type."""
        return self.__class__(self.name)

    def to_dict(self):
        """Get data type as a dictionary."""
        return {
            'name': self.name,
            'data_type': self.__class__.__name__,
            'base_unit': self.units[0],
            'type': 'DataTypeBase'
        }

    # TODO: Un-comment the numeric check once we have gotten rid of the DataPoint class
    # Presently, I can't add a check for DataPoint type because it's outside the module
    def _is_numeric(self, values):
        """Check to be sure values are numbers before doing numerical operations."""
        if len(values) > 0:
            assert isinstance(values[0], (float, int)), \
                "values must be numbers to perform math operations. Got {}".format(
                    type(values[0]))
        return True

    def _to_unit_base(self, base_unit, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        self._is_numeric(values)
        namespace = {'self': self, 'values': values}
        if not from_unit == base_unit:
            self.is_unit_acceptable(from_unit, True)
            statement = '[self._{}_to_{}(val) for val in values]'.format(
                self._clean(from_unit), self._clean(base_unit))
            values = eval(statement, namespace)
            namespace['values'] = values
        if not unit == base_unit:
            self.is_unit_acceptable(unit, True)
            statement = '[self._{}_to_{}(val) for val in values]'.format(
                self._clean(base_unit), self._clean(unit))
            values = eval(statement, namespace)
        return values

    def _clean(self, unit):
        """Clean out special characters from unit abbreviations."""
        return unit.replace(
            '/', '_').replace(
                '-', '').replace(
                    ' ', '').replace(
                        '%', 'pct')

    @property
    def name(self):
        """The data type name."""
        if self._name is None:
            return re.sub(r"(?<=\w)([A-Z])", r" \1", self.__class__.__name__)
        else:
            return self._name

    @property
    def units(self):
        """A tuple of all acceptable units for the data type."""
        return self._units

    @property
    def si_units(self):
        """A tuple of acceptable si_units for the data type."""
        return self._si_units

    @property
    def ip_units(self):
        """A tuple of acceptable ip_units for the data type."""
        return self._ip_units

    @property
    def min(self):
        """The minimum possible value of the data type."""
        return self._min

    @property
    def max(self):
        """The maximum possible value of the data type."""
        return self._max

    @property
    def abbreviation(self):
        """The abbreviation of the data type."""
        return self._abbreviation

    @property
    def unit_descr(self):
        """A description of the data type units.

        This is useful if numerical values of the units relate to specific categories.
        (eg. -1 = Cold, 0 = Neutral, +1 = Hot) (eg. 0 = False, 1 = True).
        """
        return self._unit_descr

    @property
    def point_in_time(self):
        """Whether the data type is point_in_time."""
        return self._point_in_time

    @property
    def cumulative(self):
        """Whether the data type is cumulative."""
        return self._cumulative

    @property
    def isDataType(self):
        """Return True."""
        return True

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Return Ladybug data type as a string."""
        return self.name


class _DataTypeEnumeration(object):
    """Enumerates all data types, base types, and units."""
    _TYPES = {}
    _BASETYPES = {}
    _UNITS = {}
    _GENERICTYPE = None

    def __init__(self, import_modules=True):
        if import_modules is True:
            self._import_modules()

        for clss in DataTypeBase.__subclasses__():
            if clss.__name__ != 'GenericType':
                self._TYPES[clss.__name__] = clss
                self._BASETYPES[clss.__name__] = clss
                self._UNITS[clss.__name__] = clss._units
                for subclss in self._all_subclasses(clss):
                    self._TYPES[subclss.__name__] = subclss
            else:
                self._GENERICTYPE = clss

    @property
    def types(self):
        """A tuple indicating all currently supported data types."""
        return tuple(sorted(self._TYPES.keys()))

    @property
    def base_types(self):
        """A tuple indicating all base types.

        Base types are the data types on which unit systems are defined.
        """
        return tuple(sorted(self._BASETYPES.keys()))

    @property
    def units(self):
        """A dictionary containing all currently supported units.

        The keys of this dictionary are the base types (eg. 'Temperature').
        """
        return self._UNITS

    @property
    def types_dict(self):
        """A dictionary containing pointers to the classes of each data type.

        The keys of this dictionary are the data types.
        """
        return self._TYPES

    def _import_modules(self):
        root_dir = dirname(__file__)
        modules = listdir(dirname(__file__))
        modules = [join(root_dir, mod) for mod in modules]
        importable = ['.{}'.format(basename(f)[:-3]) for f in modules
                      if isfile(f) and f.endswith('.py')
                      and not f.endswith('__init__.py')
                      and not f.endswith('base.py')]
        for mod in importable:
            import_module(mod, 'ladybug.datatype')

    def _all_subclasses(self, clss):
        return set(clss.__subclasses__()).union(
            [s for c in clss.__subclasses__() for s in self._all_subclasses(c)])
